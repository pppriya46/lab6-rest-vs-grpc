#!/usr/bin/env python3

from concurrent import futures
import argparse
import base64
import io
import logging

import grpc
from PIL import Image

import lab6_pb2
import lab6_pb2_grpc


class Lab6Servicer(lab6_pb2_grpc.Lab6Servicer):

    def add(self, request, context):
        return lab6_pb2.addReply(sum=request.a + request.b)

    def rawImage(self, request, context):
        try:
            img = Image.open(io.BytesIO(request.img))
            return lab6_pb2.imageReply(width=img.size[0], height=img.size[1])
        except Exception:
            return lab6_pb2.imageReply(width=0, height=0)

    def dotProduct(self, request, context):
        if len(request.a) != len(request.b):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT,
                          'vectors must be the same length')
        total = sum(x * y for x, y in zip(request.a, request.b))
        return lab6_pb2.dotProductReply(dotproduct=total)

    def jsonImage(self, request, context):
        try:
            img = Image.open(io.BytesIO(base64.b64decode(request.img)))
            return lab6_pb2.imageReply(width=img.size[0], height=img.size[1])
        except Exception:
            return lab6_pb2.imageReply(width=0, height=0)


def serve(port):
    options = [
        ('grpc.max_receive_message_length', 16 * 1024 * 1024),
        ('grpc.max_send_message_length', 16 * 1024 * 1024),
    ]
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), options=options)
    lab6_pb2_grpc.add_Lab6Servicer_to_server(Lab6Servicer(), server)
    server.add_insecure_port(f'0.0.0.0:{port}')
    server.start()
    print(f"gRPC server listening on port {port}")
    server.wait_for_termination()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='gRPC server')

    parser.add_argument(
        '-p', '--port',
        type=int,
        default=50051,
        help='Port on which to run the server (default: 50051)'
    )

    args = parser.parse_args()

    logging.basicConfig()
    serve(args.port)
