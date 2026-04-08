# Development

## Build Image for AWS
`docker build -t <namespace>/<repo_name> . -f Dockerfile.aws.lambda`

Example, if your namespace on aws is `gordonfreeman`, and the repo name is `black_mesa`, then the command is:
`docker build -t gordonfreeman/black_mesa . -f Dockerfile.aws.lambda`

Since I have replaced the content of `backend/Dockerfile` with the content of `backend/Dockerfile.aws.lambda`, you can omit the `-f` flag and its argument.

Like so:
`docker build -t gordonfreeman/black_mesa .`
