from flask import Flask, render_template, request, jsonify, send_file
import pytz
from datetime import datetime, timedelta
import os
import traceback
import zipfile

app = Flask(__name__)

# Common timezones for dropdown
COMMON_TIMEZONES = [
    'US/Eastern', 'US/Central', 'US/Pacific', 'US/Mountain',
    'Europe/Paris', 'Europe/Lisbon', 'Asia/Kolkata', 'Asia/Singapore',
    'Australia/Sydney', 'Asia/Tokyo', 'Asia/Seoul', 'Pacific/Honolulu',
    'Europe/Istanbul', 'Europe/London', 'Europe/Athens', 'Asia/Karachi',
    'Asia/Manila', 'Australia/Adelaide', 'America/Halifax', 'Asia/Makassar',
    'Asia/Jakarta', 'America/Argentina/Buenos_Aires', 'America/Bogota',
    'Africa/Johannesburg', 'Pacific/Auckland', 'Africa/Lagos',
    'Africa/Nairobi', 'Australia/Perth'
]

# Mapping of timezone abbreviations for display
TZ_ABBREVIATIONS = {
    'US/Pacific': 'PST/PDT', 'US/Mountain': 'MST/MDT', 'US/Central': 'CST/CDT', 'US/Eastern': 'EST/EDT',
    'Europe/London': 'GMT/BST', 'Europe/Paris': 'CET/CEST', 'Europe/Berlin': 'CET/CEST',
    'Asia/Tokyo': 'JST', 'Australia/Sydney': 'AEDT/AEST', 'America/Sao_Paulo': 'BRT',
    'Asia/Kolkata': 'IST', 'America/Argentina/Buenos_Aires': 'ART', 'Europe/Istanbul': 'TRT',
    'America/Halifax': 'AST/ADT', 'Europe/Malta': 'MT', 'Asia/Jakarta': 'WIB',
    'Pacific/Samoa': 'SST', 'Asia/Seoul': 'KST', 'America/Manaus': 'AMT',
    'Asia/Manila': 'PHT', 'Australia/Adelaide': 'ACST', 'Asia/Makassar': 'WITA',
    'America/Bogota': 'COT', 'Africa/Johannesburg': 'SAST', 'Pacific/Auckland': 'NZDT/NZST',
    'Africa/Lagos': 'WAT', 'Africa/Nairobi': 'EAT', 'Australia/Perth': 'AWST'
}

# Mapping of common abbreviations to full timezone names
def get_full_timezone(tz_abbr):
    mapping = {
        'PST': 'US/Pacific', 'MST': 'US/Mountain', 'CST': 'US/Central', 'EST': 'US/Eastern',
        'GMT': 'Europe/London', 'CET': 'Europe/Paris', 'JST': 'Asia/Tokyo', 'AEDT': 'Australia/Sydney', 'BRT': 'America/Sao_Paulo',
        'IST': 'Asia/Kolkata', 'PDT': 'US/Pacific', 'MDT': 'US/Mountain', 'CDT': 'US/Central', 'EDT': 'US/Eastern',
        'ART': 'America/Argentina/Buenos_Aires', 'TRT': 'Europe/Istanbul', 'AST': 'America/Halifax', 'MT': 'Europe/Malta',
        'WIB': 'Asia/Jakarta', 'SST': 'Pacific/Samoa', 'KST': 'Asia/Seoul', 'AMT': 'America/Manaus',
        'PHT': 'Asia/Manila', 'AEST': 'Australia/Sydney', 'ACST': 'Australia/Adelaide', 'WITA': 'Asia/Makassar',
        'COT': 'America/Bogota', 'SAST': 'Africa/Johannesburg', 'BST': 'Europe/London', 'ADT': 'America/Halifax',
        'NZDT': 'Pacific/Auckland', 'WAT': 'Africa/Lagos', 'CEST': 'Europe/Paris', 'EAT': 'Africa/Nairobi',
        'AWST': 'Australia/Perth'
    }
    tz_abbr = tz_abbr.upper()
    return mapping.get(tz_abbr, tz_abbr if tz_abbr in pytz.all_timezones else None)

def get_timezone_abbr(tz_name):
    return TZ_ABBREVIATIONS.get(tz_name, tz_name.split('/')[-1] if '/' in tz_name else tz_name)

def get_time_difference(base_tz, target_tz):
    try:
        base_timezone = pytz.timezone(base_tz)
        target_timezone = pytz.timezone(target_tz)
        # Use a naive datetime for offset calculation
        now = datetime.now()
        base_offset = base_timezone.utcoffset(now).total_seconds() / 3600 if base_timezone.utcoffset(now) else 0
        target_offset = target_timezone.utcoffset(now).total_seconds() / 3600 if target_timezone.utcoffset(now) else 0
        return target_offset - base_offset
    except pytz.exceptions.UnknownTimeZoneError:
        return None

@app.route('/')
def index():
    return render_template('index.html', timezones=COMMON_TIMEZONES, abbr=get_timezone_abbr)

@app.route('/compare', methods=['POST'])
def compare():
    try:
        base_tz = request.form.get('base_timezone', '').strip()
        if not base_tz or base_tz not in pytz.all_timezones:
            return jsonify({'error': 'Invalid base timezone'}), 400

        base_time_str = request.form.get('base_time', '').strip()
        if base_time_str:
            try:
                # Parse time in HH:MM format and combine with today's date
                base_time = datetime.strptime(base_time_str, '%H:%M')
                today = datetime.now().date()
                base_time = datetime.combine(today, base_time.time())
                print(f"Using provided base time: {base_time_str} in {base_tz}")
            except ValueError as e:
                print(f"Error parsing time: {e}")
                base_time = datetime.now()
        else:
            base_time = datetime.now()
            print(f"Using current time in {base_tz}: {base_time.strftime('%H:%M:%S')}")

        base_timezone = pytz.timezone(base_tz)
        base_time = base_timezone.localize(base_time)
        print(f"Localized base time: {base_time.strftime('%H:%M:%S %Z')}")

        # Handle both comma and newline separated timezones
        tz_input = request.form.get('timezones', '').strip()
        timezones = []
        original_timezones = []
        if tz_input:
            # Split by newline first (for spreadsheet copy-paste), then by comma
            lines = tz_input.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    tz_list = [tz.strip().upper() for tz in line.split(',') if tz.strip()]
                    original_timezones.extend(tz_list)
                    timezones.extend(tz_list)
            # Standardize timezone abbreviations to full names
            standardized_tzs = []
            skipped_count = 0
            for tz in timezones:
                full_tz = get_full_timezone(tz)
                if full_tz:
                    standardized_tzs.append(full_tz)
                else:
                    skipped_count += 1
            timezones = standardized_tzs
            skipped_notice = f"Skipped {skipped_count} invalid or unmapped timezone entries from processing." if skipped_count > 0 else ""
        else:
            # If no custom timezones provided, use common timezones
            timezones = COMMON_TIMEZONES
            skipped_notice = ""
            original_timezones = timezones

        if not timezones:
            return jsonify({'error': 'No valid timezones provided'}), 400

        # Maintain order of unique timezones based on first appearance in input
        unique_original_tzs_ordered = []
        for tz in original_timezones:
            if tz not in unique_original_tzs_ordered:
                unique_original_tzs_ordered.append(tz)
        unique_tzs_ordered = []
        for tz in timezones:
            if tz not in unique_tzs_ordered:
                unique_tzs_ordered.append(tz)
        tz_counts = {tz: original_timezones.count(tz) for tz in unique_original_tzs_ordered}

        results = []
        skipped_timezones = []
        processed_tzs = set()
        # Process in order of original input, mapping to standardized if available
        for orig_tz in unique_original_tzs_ordered:
            mapped_tz = get_full_timezone(orig_tz)
            if mapped_tz and mapped_tz in pytz.all_timezones and mapped_tz not in processed_tzs:
                diff = get_time_difference(base_tz, mapped_tz)
                if diff is not None:
                    target_timezone = pytz.timezone(mapped_tz)
                    target_time = base_time.astimezone(target_timezone)
                    print(f"Timezone: {mapped_tz}, Local Time: {target_time.strftime('%H:%M:%S %Z')}")
                    results.append({
                        'timezone': mapped_tz,
                        'original': orig_tz,
                        'abbr': get_timezone_abbr(mapped_tz),
                        'difference': diff,
                        'current_time': target_time.strftime('%I:%M %p'),
                        'count': tz_counts.get(orig_tz, 1)
                    })
                    processed_tzs.add(mapped_tz)
            elif orig_tz not in processed_tzs and not any(get_full_timezone(t) == orig_tz for t in original_timezones):
                skipped_timezones.append({
                    'timezone': orig_tz,
                    'original': orig_tz,
                    'abbr': orig_tz,
                    'difference': 'N/A',
                    'current_time': 'N/A',
                    'count': tz_counts.get(orig_tz, 1)
                })
                processed_tzs.add(orig_tz)
        results.extend(skipped_timezones)

        if not results and not skipped_timezones:
            return jsonify({'error': 'No timezones provided'}), 400

        return jsonify({'results': results, 'notice': skipped_notice})
    except Exception as e:
        print(f"Error in compare endpoint: {e}")
        traceback.print_exc()
        return jsonify({'error': f"Server error: {str(e)}"}), 500

@app.route('/analyze_timezones', methods=['POST'])
def analyze_timezones():
    base_tz = request.form.get('base_timezone', '').strip()
    if not base_tz or base_tz not in pytz.all_timezones:
        return jsonify({'error': 'Invalid base timezone'}), 400

    tz_input = request.form.get('timezones', '').strip()
    if not tz_input:
        return jsonify({'error': 'No timezones provided'}), 400

    # Handle both comma and newline separated timezones
    timezones = []
    original_timezones = []
    lines = tz_input.split('\n')
    for line in lines:
        line = line.strip()
        if line:
            tz_list = [tz.strip() for tz in line.split(',') if tz.strip()]
            original_timezones.extend(tz_list)
            timezones.extend(tz_list)
    if not timezones:
        return jsonify({'error': 'No valid timezones provided'}), 400

    # Standardize timezone abbreviations to full names
    standardized_tzs = []
    skipped_count = 0
    for tz in timezones:
        full_tz = get_full_timezone(tz)
        if full_tz:
            standardized_tzs.append(full_tz)
        else:
            skipped_count += 1
    timezones = standardized_tzs

    skipped_notice = f"Skipped {skipped_count} invalid or unmapped timezone entries from processing." if skipped_count > 0 else ""

    # Maintain order of unique timezones based on first appearance in input
    unique_original_tzs_ordered = []
    for tz in original_timezones:
        if tz not in unique_original_tzs_ordered:
            unique_original_tzs_ordered.append(tz)
    unique_tzs_ordered = []
    for tz in timezones:
        if tz not in unique_tzs_ordered:
            unique_tzs_ordered.append(tz)
    tz_counts = {tz: original_timezones.count(tz) for tz in unique_original_tzs_ordered}

    results = []
    skipped_timezones = []
    processed_tzs = set()
    # Process in order of original input, mapping to standardized if available
    for orig_tz in unique_original_tzs_ordered:
        mapped_tz = get_full_timezone(orig_tz)
        if mapped_tz and mapped_tz in pytz.all_timezones and mapped_tz not in processed_tzs:
            diff = get_time_difference(base_tz, mapped_tz)
            if diff is not None:
                results.append({
                    'timezone': mapped_tz,
                    'original': orig_tz,
                    'abbr': get_timezone_abbr(mapped_tz),
                    'count': tz_counts.get(orig_tz, 1),
                    'difference': diff
                })
                processed_tzs.add(mapped_tz)
        elif orig_tz not in processed_tzs and not any(get_full_timezone(t) == orig_tz for t in original_timezones):
            skipped_timezones.append({
                'timezone': orig_tz,
                'original': orig_tz,
                'abbr': orig_tz,
                'count': tz_counts.get(orig_tz, 1),
                'difference': 'N/A'
            })
            processed_tzs.add(orig_tz)
    results.extend(skipped_timezones)

    if not results and not skipped_timezones:
        return jsonify({'error': 'No valid timezones found in input'}), 400

    return jsonify({'results': results, 'notice': skipped_notice})

@app.route('/calculate_shift', methods=['POST'])
def calculate_shift():
    data = request.form
    base_tz = data.get('base_timezone', 'UTC')
    base_time_str = data.get('base_time', '')
    timezones_str = data.get('timezones', '')

    try:
        base_tzinfo = pytz.timezone(base_tz)
    except pytz.exceptions.UnknownTimeZoneError:
        return jsonify({'error': f'Invalid base timezone: {base_tz}'})

    if base_time_str:
        try:
            base_time = datetime.strptime(base_time_str, '%H:%M').replace(tzinfo=base_tzinfo)
            today = datetime.now(base_tzinfo).date()
            base_time = datetime.combine(today, base_time.time())
            base_time = base_tzinfo.localize(base_time)
            print(f"Using provided base time: {base_time_str} in {base_tz}, Localized: {base_time.strftime('%H:%M:%S %Z')}")
        except ValueError:
            return jsonify({'error': 'Invalid time format. Use HH:MM'})
    else:
        base_time = datetime.now(base_tzinfo)
        print(f"Using current time in {base_tz}: {base_time.strftime('%H:%M:%S %Z')}")

    if timezones_str.strip():
        tz_list = []
        lines = timezones_str.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                tz_entries = [tz.strip().upper() for tz in line.split(',') if tz.strip()]
                for tz in tz_entries:
                    full_tz = get_full_timezone(tz)
                    if full_tz:
                        tz_list.append((tz, full_tz))
                    else:
                        tz_list.append((tz, tz))
        results = []
        seen = set()
        for original, tz in tz_list:
            if tz in seen:
                continue
            seen.add(tz)
            try:
                tzinfo = pytz.timezone(tz)
                base_time_local = base_time.astimezone(tzinfo)
                # Calculate shift times
                # Assume shift starts at 9:00 AM local time and ends at 5:30 PM local time
                shift_start_local = base_time_local.replace(hour=9, minute=0, second=0, microsecond=0)
                if base_time_local < shift_start_local:
                    shift_start_local = shift_start_local - timedelta(days=1)
                shift_end_local = shift_start_local.replace(hour=17, minute=30)
                if shift_end_local < shift_start_local:
                    shift_end_local = shift_end_local + timedelta(days=1)
                hours_left = ((shift_end_local - base_time_local).total_seconds() / 3600.0)
                # Cap hours left at 8 hours due to 30-minute lunch break
                hours_left = min(hours_left, 8.0)
                minutes_left = hours_left * 60 if hours_left > 0 else 'Shift Ended'
                if hours_left <= 0:
                    hours_left = 'Shift Ended'
                    minutes_left = 'Shift Ended'
                    shift_end_local_str = 'Shift Ended'
                else:
                    shift_end_base = shift_end_local.astimezone(base_tzinfo)
                    shift_end_local_str = shift_end_base.strftime('%I:%M %p').lstrip('0')
                print(f"Timezone: {tz}, Current Local Time: {base_time_local.strftime('%H:%M:%S %Z')}, Shift End Local: {shift_end_local.strftime('%H:%M:%S %Z') if hours_left != 'Shift Ended' else 'N/A'}, Hours Left: {hours_left}, Minutes Left: {minutes_left}")
                results.append({
                    'abbr': get_timezone_abbr(tz) if tz in pytz.all_timezones else original,
                    'timezone': tz,
                    'hours_left': hours_left,
                    'minutes_left': minutes_left,
                    'shift_end_time': shift_end_local_str,
                    'count': sum(1 for o, t in tz_list if t == tz)
                })
            except pytz.exceptions.UnknownTimeZoneError:
                results.append({
                    'abbr': original,
                    'timezone': f"{original} (Unrecognized)",
                    'hours_left': 'N/A',
                    'minutes_left': 'N/A',
                    'shift_end_time': 'N/A',
                    'count': sum(1 for o, t in tz_list if o == original and t == tz)
                })
    else:
        results = []
        for tz in COMMON_TIMEZONES:
            tzinfo = pytz.timezone(tz)
            base_time_local = base_time.astimezone(tzinfo)
            # Calculate shift times
            # Assume shift starts at 9:00 AM local time and ends at 5:30 PM local time
            shift_start_local = base_time_local.replace(hour=9, minute=0, second=0, microsecond=0)
            if base_time_local < shift_start_local:
                shift_start_local = shift_start_local - timedelta(days=1)
            shift_end_local = shift_start_local.replace(hour=17, minute=30)
            if shift_end_local < shift_start_local:
                shift_end_local = shift_end_local + timedelta(days=1)
            hours_left = ((shift_end_local - base_time_local).total_seconds() / 3600.0)
            # Cap hours left at 8 hours due to 30-minute lunch break
            hours_left = min(hours_left, 8.0)
            minutes_left = hours_left * 60 if hours_left > 0 else 'Shift Ended'
            if hours_left <= 0:
                hours_left = 'Shift Ended'
                minutes_left = 'Shift Ended'
                shift_end_local_str = 'Shift Ended'
            else:
                shift_end_base = shift_end_local.astimezone(base_tzinfo)
                shift_end_local_str = shift_end_base.strftime('%I:%M %p').lstrip('0')
            print(f"Timezone: {tz}, Current Local Time: {base_time_local.strftime('%H:%M:%S %Z')}, Shift End Local: {shift_end_local.strftime('%H:%M:%S %Z') if hours_left != 'Shift Ended' else 'N/A'}, Hours Left: {hours_left}, Minutes Left: {minutes_left}")
            results.append({
                'abbr': get_timezone_abbr(tz),
                'timezone': tz,
                'hours_left': hours_left,
                'minutes_left': minutes_left,
                'shift_end_time': shift_end_local_str,
                'count': 1
            })
    return jsonify({'results': results})

@app.route('/download_assets')
def download_assets():
    zip_filename = 'Timezone_Shift_Calculator_Assets.zip'
    zip_path = os.path.join(os.getcwd(), 'static', zip_filename)
    
    if not os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            base_dir = os.getcwd()
            # Add app.py
            app_path = os.path.join(base_dir, 'TimezoneComparator', 'app.py')
            if os.path.exists(app_path):
                zipf.write(app_path, 'TimezoneComparator/app.py')
            # Add templates
            templates_dir = os.path.join(base_dir, 'TimezoneComparator', 'templates')
            if os.path.exists(templates_dir):
                for root, _, files in os.walk(templates_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, base_dir)
                        arcname = os.path.join('TimezoneComparator', rel_path)
                        zipf.write(file_path, arcname)
            # Add static files
            static_dir = os.path.join(base_dir, 'TimezoneComparator', 'static')
            if os.path.exists(static_dir):
                for root, _, files in os.walk(static_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, base_dir)
                        arcname = os.path.join('TimezoneComparator', rel_path)
                        zipf.write(file_path, arcname)
            # Add requirements.txt if it exists
            req_path = os.path.join(base_dir, 'TimezoneComparator', 'requirements.txt')
            if os.path.exists(req_path):
                zipf.write(req_path, 'TimezoneComparator/requirements.txt')
            # Add README.md if it exists
            readme_path = os.path.join(base_dir, 'TimezoneComparator', 'README.md')
            if os.path.exists(readme_path):
                zipf.write(readme_path, 'TimezoneComparator/README.md')
    
    return send_file(zip_path, as_attachment=True, download_name=zip_filename)

@app.route('/get_code/<path:filepath>')
def get_code(filepath):
    try:
        full_path = os.path.join(os.getcwd(), 'TimezoneComparator', filepath)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content, 200, {'Content-Type': 'text/plain'}
        else:
            return 'File not found', 404
    except Exception as e:
        return f'Error reading file: {str(e)}', 500

if __name__ == '__main__':
    app.run(debug=True)
