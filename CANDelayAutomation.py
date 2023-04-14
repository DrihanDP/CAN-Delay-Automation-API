from saleae import automation
import os
import os.path
from datetime import datetime
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
        capture_mode=automation.TimedCaptureMode(duration_seconds=120.0),
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
        output_dir = os.path.join(os.getcwd(), f'C:\\Users\\Drihan Du Preez\\Documents\\Automation tests\\{datetime.now().strftime("%d-%m-%y_%H-%M-%S")}')
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
standard_channels = [
    "0x0000000000000301",
    "0x0000000000000302",
    "0x0000000000000303",
    "0x0000000000000304",
    "0x0000000000000305",
    "0x0000000000000306",
    "0x0000000000000307",
    "0x0000000000000308",
    "0x0000000000000309",
    "0x0000000000000314",
]

with open(csv_file_path, 'r') as f:
    lines = f.readlines()

for line in lines:
    splitLine = line.strip("\n").split(",")
    if splitLine[1] == '1' and first_0 == True:
        trigger_on_time.append(splitLine[0])
    elif first_0 == False:
        if splitLine[1] == '0':
            first_0 = True
        else:
            pass

with open(analyzer_export_filepath, 'r') as f:
    lines = f.readlines()

for line in lines:
    splitLine = line.strip("\n").split(",")
    if 'identifier_field' in splitLine[1]:
        last_id = splitLine[3]
        if last_id not in standard_channels:
            data_list.clear()
    elif 'data_field' in splitLine[1] and last_id in standard_channels:
        data_list.append(splitLine[4])
        if len(data_list) == 8:
            print(last_id, data_list)
            data_list.clear()