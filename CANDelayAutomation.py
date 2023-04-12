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
        digital_sample_rate=500_000,
    )

    # Start recording for 2 minutes
    capture_configuration = CaptureConfiguration(
        capture_mode=automation.TimedCaptureMode(duration_seconds=120.0)
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
           '3i PPS': 0,
           'UBLOX PPS': 1,
           'CAN High': 2,
           'CAN Low': 3,
        #    'Bits per Transfer': '8 Bits per Transfer (Standard)'
        })

        # Store output in a timestamped directory
        output_dir = os.path.join(os.getcwd(), f'C:\Users\Drihan Du Preez\Documents\Automation tests-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}')
        os.makedirs(output_dir)

        print("\nTest complete, exporting files...")

        # Export analyzer data to a CSV file
        analyzer_export_filepath = os.path.join(output_dir, 'can_export.csv')
        capture.export_data_table(
           filepath=analyzer_export_filepath,
           analyzers=[can_analyzer]
        )

        # Export raw digital data to a CSV file
        capture.export_raw_data_csv(directory=output_dir, digital_channels=[0, 1, 2, 3])

        # Finally, save the capture to a file
        capture_filepath = os.path.join(output_dir, 'CAN delay capture.sal')
        capture.save_capture(filepath=capture_filepath)

        print(f"\nExport complete, files can be found in...\n{output_dir}")