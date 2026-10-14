# Lab 6 - REST vs gRPC results

Time per operation in milliseconds. The client ran on `lab6-a` (`e2-standard-2`, `us-west1-a`) in every test, using internal IPs.

- **Local**: server and client both on `lab6-a`, host `localhost`, 1000 reps.
- **Same-Zone**: server on `lab6-b` (`us-west1-a`), 1000 reps.
- **Different Region**: server on `lab6-eu` (`europe-west3-a`, Frankfurt), 100 reps.

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

PING is the average of 20 pings (the local one is to `localhost`).

## What I noticed

When the client and server are close together, gRPC is faster on the small calls. A REST `add` took about 2.6-2.9 ms and a gRPC `add` about 0.7-1.0 ms, so roughly 3x. It isn't really about the network here. Going from local to same-zone only added about 0.3 ms to either one, which matches the 0.36 ms ping. The difference is the cost of each request itself: my REST client opens a brand new TCP connection for every query and Flask has to parse HTTP and JSON every time, while gRPC keeps one connection open and sends small protobuf messages.

The image calls surprised me. With low latency, gRPC was faster for `jsonimg` (18 vs 27 ms locally) but slower for `rawimg` (12 vs 5 ms locally). I didn't profile it, but my guess is that Python's protobuf and gRPC code copies and splits a 1.6 MB message, while Flask just reads the raw body in one go.

Once the server is in Frankfurt, latency takes over completely. The ping is about 160 ms, and the results line up with round trips. REST `add` took 339 ms, which is about 2 round trips: one to open the new connection and one for the request and reply. gRPC `add` took 162 ms, about 1 round trip, because the connection was already open. That's the biggest takeaway for me: gRPC can't do better than one round trip, but REST pays for the connection setup on every single query.

The gap gets even bigger with the images. REST needed about 1.6 s for `rawimg` and `jsonimg` (roughly 10 round trips) while gRPC needed about 0.2 s. My explanation is that every REST call starts a fresh connection, so each 1.6-2 MB upload begins with a small TCP window and takes many round trips to speed up. The gRPC connection has already been used, so it can send the data much faster. I'm inferring this from the numbers and didn't measure it. `jsonimg` is also bigger on the wire than `rawimg` because base64 adds about 33%, but that mattered a lot less than the latency.

So overall: with low latency, gRPC wins on small calls and the large-image results are mixed. With high latency, gRPC is about 2x faster on small calls and about 8x faster on the large ones, mostly because it reuses its connection.

## Notes

- The different-region tests used 100 reps instead of 1000 so they wouldn't take forever. Every number is from a single run.
- The gRPC client makes one untimed warm-up call so connection setup isn't counted. The REST client uses `requests.post`, which opens a new connection for each query.
- gRPC `dotproduct` uses 32-bit floats like the handout says, so its answers differ slightly from REST's 64-bit ones.
