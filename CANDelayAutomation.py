from saleae import automation
import os
import os.path
import datetime
from saleae.automation import *


# Connect to the running Logic 2 Application on port `10430`.
# Alternatively you can use automation.Manager.launch() to launch a new Logic 2 process - see
# the API documentation for more details.
# Using the `with` statement will automatically call manager.close() when exiting the scope. If you
# want to use `automation.Manager` outside of a `with` block, you will need to call `manager.close()` manually.
with Manager.connect(port=10430) as manager:

    # Configure the capturing device to record on digital channels 0, 1, 2, and 3,
    # with a sampling rate of 10 MSa/s, and a logic level of 3.3V.
    # The settings chosen here will depend on your device's capabilities and what
    # you can configure in the Logic 2 UI.
    device_configuration = LogicDeviceConfiguration(
        enabled_digital_channels=[0, 1, 2, 3],
        digital_sample_rate=2000000,
    )

    # Start recording for 2 minutes
    capture_configuration = CaptureConfiguration(
        capture_mode=automation.TimedCaptureMode(duration_seconds=30.0),
    )

    # Start a capture - the capture will be automatically closed when leaving the `with` block
    with manager.start_capture(
            # device_id = 'A4B500C3BF54259', # This can be set or left 
            device_configuration=device_configuration,
            capture_configuration=capture_configuration) as capture:

        print("\nTest started...")

        # Wait until the capture has finished
        # This will take about 5 seconds because we are using a timed capture mode
        capture.wait()

        # Add an analyzer to the capture
        # Note: The simulator output is not actual SPI data

        can_analyzer = capture.add_analyzer('CAN', label=f'Test Analyzer', settings={
            "CAN": 2,
            "Bit Rate (Bits/s)": 500000
        })

        data_configuration = DataTableExportConfiguration(
        can_analyzer,
        radix=automation.RadixType.HEXADECIMAL
        )

        # Store output in a timestamped directory
        output_dir = os.path.join(os.getcwd(), f'C:\\Users\\Drihan Du Preez\\Documents\\Automation tests\\{datetime.datetime.now().strftime("%d-%m-%y_%H-%M-%S")}')
        os.makedirs(output_dir)

        print("\nTest complete, exporting files...")

        # Export analyzer data to a CSV text file
        analyzer_export_filepath = os.path.join(output_dir, 'can_export.txt')
        capture.export_data_table(
           filepath=analyzer_export_filepath,
           analyzers=[can_analyzer, data_configuration],
           columns=["Type", "Start", "identifier", "data"],
        )

        # Export raw digital data to a CSV file 
        capture.export_raw_data_csv(directory=output_dir, digital_channels=[1])
        csv_file_path = output_dir + "\\digital.csv"
        # Finally, save the capture to a file
        capture_filepath = os.path.join(output_dir, 'CAN delay capture.sal')
        capture.save_capture(filepath=capture_filepath)

        print(f"\nExport complete, files can be found in...\n{output_dir}")
        print()

first_0 = False
trigger_on_time = []
data_list = []
stahle_UTC_list = []
stahle_speed_list = []
stahle_heading_list = []
previous_speed = None
previous_heading = None
speed = None
heading = None

with open(csv_file_path, 'r') as f:
    lines = f.readlines()

for line in lines:
    splitLine = line.strip("\n").split(",")
    if splitLine[1] == '1' and first_0 == True:
        trigger_on_time.append(float(splitLine[0]))
    elif first_0 == False:
        if splitLine[1] == '0':
            first_0 = True
        else:
            pass

# print(trigger_on_time)

with open(analyzer_export_filepath, 'r') as f:
    lines = f.readlines()

for line in lines:
    splitLine = line.strip("\n").split(",")
    if 'identifier_field' in splitLine[1]:
        last_id = splitLine[3]
        if last_id == "0x0000000000000301":
            ID301Time = float(splitLine[2])
            for value in trigger_on_time:
                if abs(value - ID301Time) <= 0.001:
                    closest_301_time = ID301Time
                    break
        elif last_id == "0x0000000000000302":
            ID302Time = splitLine[2]
        elif last_id == "0x0000000000000303":
            ID303Time = splitLine[2]
    elif 'data_field' in splitLine[1]:
        data_list.append(splitLine[4][2:])
        if len(data_list) == 8:
            if last_id == "0x0000000000000301":
                hex_join = "".join(data_list[1:4])
                converted_hex = int(hex_join, 16)
                UTCTime = datetime.timedelta(seconds=(int(converted_hex) * 0.01))
                data_list.clear()
            elif last_id == "0x0000000000000302":
                hex_join = "".join(data_list[4:6])
                converted_hex = int(hex_join, 16)
                speed = converted_hex * 0.01 * 1.852
                hex_join = "".join(data_list[6:])
                converted_hex = int(hex_join, 16)
                heading = converted_hex * 0.01
                data_list.clear()
            elif last_id == "0x0000000000000303":
                val = bin(int(("0x" + data_list[7]), 16))
                leading_zero = "0" * (10 - len(val))
                bin_val = leading_zero + val[2:]
                info = []
                if bin_val[3] == "1":
                    info.append("Brake test started")
                if bin_val[4] == "1":
                    info.append("Brake trigger active")
                if bin_val[5] == "1":
                    info.append("DGPS Active")
                if bin_val[6] == "1":
                    info.append("Dual Antenna Active")
                if bin_val[3] == "0" and bin_val[4] == "0" and bin_val[5] == "0" and bin_val[6] == "0":
                    info.append("No additional information")
                data_list.clear()
            elif last_id == "0x000000000000009C":
                hex_values = data_list[0:4]
                hex_values.reverse()
                hex_join = "".join(hex_values)
                converted_hex = int(hex_join, 16)
                stahle_UTC = datetime.timedelta(seconds=(int(converted_hex) * 0.01))
                stahle_UTC_list.append(stahle_UTC)
                data_list.clear()
                try:
                    if UTCTime in stahle_UTC_list:
                        stahle_UTC_list.remove(UTCTime)
                        # print(f"Time since midnight delay - {len(stahle_UTC_list)} samples")
                except:
                    pass
            elif last_id == "0x0000000000000066":
                hex_values = data_list[0:4]
                hex_values.reverse()
                hex_join = "".join(hex_values)
                stahle_speed = int(hex_join, 16)
                stahle_speed_list.append(stahle_speed)
                try:
                    if speed == stahle_speed_list[0] and speed != previous_speed:
                        del stahle_speed_list[0]
                    else:
                        if speed > previous_speed:
                            if speed > stahle_speed_list[0]:
                                stahle_speed_list.clear()
                        elif speed < previous_speed:
                            if speed < stahle_speed_list[0]:
                                stahle_speed_list.clear()
                        else:
                            if speed == stahle_speed_list[0]:
                                stahle_speed_list.clear()
                    # print(f"Speed delay - {len(stahle_speed_list)}")
                except:
                    pass
                previous_speed = speed
                data_list.clear()
            elif last_id == "0x0000000000000095":
                hex_values = data_list[6:]
                hex_values.reverse()
                hex_join = "".join(hex_values)
                stahle_heading = int(hex_join, 16) * 0.01
                try:
                    if heading == stahle_heading_list[0] and heading != previous_heading:
                        del stahle_heading_list[0]
                    print(f"Heading delay - {len(stahle_heading_list)}")
                except:
                    pass
                previous_heading = heading
                data_list.clear()
            else:
                data_list.clear()