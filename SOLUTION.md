# Lab 6 - REST vs gRPC results

Time per operation in milliseconds. The client always ran on one VM in us-west1-a, and I used the internal IP addresses.

- **Local**: server and client on the same VM (localhost), 1000 reps.
- **Same-Zone**: server on a second VM in us-west1-a, 1000 reps.
- **Different Region**: server on a VM in europe-west3-a (Frankfurt), 100 reps.

|  Method 	| Local  	| Same-Zone  	|  Different Region 	|
|---	|---	|---	|---	|
|   REST add	| 2.61  	| 2.86  	| 339.0 	|
|   gRPC add	| 0.69  	| 1.02  	| 162.0 	|
|   REST rawimg	| 4.91  	| 6.36  	| 1643.4 	|
|   gRPC rawimg	| 12.02 	| 10.72 	| 194.9 	|
|   REST dotproduct	| 3.10 	| 3.20 	| 457.5 	|
|   gRPC dotproduct	| 0.83 	| 1.10 	| 165.1 	|
|   REST jsonimg	| 26.62 	| 28.50 	| 1595.3 	|
|   gRPC jsonimg	| 18.12 	| 21.74 	| 206.0 	|
|   PING        | 0.054 | 0.362 | 159.9 |

PING is the average of 20 pings.

## What I noticed

When the client and server are close together, gRPC is faster on the small calls. A REST add took about 2.6-2.9 ms and a gRPC add about 0.7-1.0 ms, so roughly 3 times faster. The network isn't the reason, since going from local to same-zone only added about 0.3 ms, which matches the ping. The difference is the work done for each request. REST opens a new connection for every query, while gRPC keeps one connection open and reuses it.

The image results were a surprise. With low latency, gRPC was faster for jsonimg but slower for rawimg (12 ms vs 5 ms locally). I didn't dig into why, but my guess is that gRPC does more work handling one big 1.6 MB message than Flask does reading the raw image.

Once the server is in Frankfurt, latency takes over. The ping is about 160 ms, and the results line up with it. A REST add took 339 ms, about 2 round trips: one to open the new connection and one for the request and reply. A gRPC add took 162 ms, about 1 round trip, because its connection was already open. gRPC can't do better than one round trip, but REST pays for opening a connection on every query.

The gap is biggest for the images. REST took about 1.6 seconds for rawimg and jsonimg, while gRPC took about 0.2 seconds. I think this is because each new REST connection starts out slow and needs many round trips to send a big image, while the gRPC connection is already warmed up. I didn't measure this, it's my explanation from the numbers.

In short, when latency is low, gRPC is better for small calls and mixed for big images. When latency is high, gRPC is about 2 times faster for small calls and about 8 times faster for big images, mostly because it reuses its connection.

## Notes

- The different-region tests used 100 reps instead of 1000 so they wouldn't take too long. Each number is from one run.
- The gRPC client makes one extra call before timing starts so the connection setup isn't counted. The REST client opens a new connection for each query.
- The gRPC dot product uses 32-bit floats like the handout says, so its answers differ slightly from REST's.
