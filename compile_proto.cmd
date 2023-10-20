set outDir="src"
python -m grpc_tools.protoc -I. --python_out=%outDir% --pyi_out=%outDir% --grpc_python_out=%outDir% proto/FrameInfo.proto proto/FrameInfoService.proto