import re

import grpc
import proto.FrameInfo_pb2 as fi_proto
import proto.FrameInfoService_pb2 as fis_proto
import proto.FrameInfoService_pb2_grpc as fis_grpc_proto
import datetime

if __name__ == '__main__':
    time_logged_use = {}
    channel = grpc.insecure_channel("localhost:50051")
    stub = fis_grpc_proto.FrameInfoServiceStub(channel)
    subscribe = fis_proto.StreamSubscribeRequest()
    subscribe.consumer_id = "test_consumer"
    incoming_frame_info: fi_proto.TimeFrameInfo
    prev_frame = None
    for incoming_frame_info in stub.Subscribe(subscribe):
        if prev_frame is None:
            print("received first frame")
            prev_frame = incoming_frame_info
            continue
        if incoming_frame_info.id != prev_frame.id + 1:
            print("Sequence error!")
            prev_frame = incoming_frame_info
            continue
        frame_datetime = datetime.datetime.utcfromtimestamp(incoming_frame_info.utc_timestamp / 1000)
        frame_date = frame_datetime.date()
        timestamp_ms = incoming_frame_info.utc_timestamp
        prev_timestamp_ms = prev_frame.utc_timestamp
        executable = incoming_frame_info.process_executable_path
        process_executable = executable.split('\\')[-1]
        title = incoming_frame_info.window_title
        # This is workaround.
        if process_executable == "Telegram.exe":
            print(f"converting telegram title '{title}' as workaround.")
            found = re.findall(r"(\(\d+\))?\s?([\w\s\d]*)(.\s\(\d+\))?", title)
            if not found:
                pass
            if len(found) == 1:
                title = found[0][1]
            else:
                print("We're fucked!")
        # We assume that we just simply spent frame_time - previous_frame_time ms in active window.
        time_spent_ms = timestamp_ms - prev_timestamp_ms
        # easiest approach is simply calculate time per process.
        # windows separation is \

        if frame_date not in time_logged_use:
            time_logged_use[frame_date] = {}
        if process_executable not in time_logged_use[frame_date]:
            time_logged_use[frame_date][process_executable] = {}
        if title not in time_logged_use[frame_date][process_executable]:
            time_logged_use[frame_date][process_executable][title] = 0
        time_logged_use[frame_date][process_executable][title] += time_spent_ms
        prev_frame = incoming_frame_info

        print("overall stats:")
        # per process
        for date, date_data in time_logged_use.items():
            print(f"{date.strftime('%A %d. %B %Y')}")
            for process_name, process_windows_info in date_data.items():
                print(f'\t{process_name=} | {sum(process_windows_info.values()) / 1000}s')
                for process_window, time_tracked in process_windows_info.items():
                    print(f'\t\t{process_window} | {time_tracked / 1000}s')
