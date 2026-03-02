# Swift Networking Baseline

Use this reference as rationale for strict enforcement decisions in the validator.

## Platform Direction

- Prefer Swift Concurrency (`async`/`await`) over callback-based APIs.
- Isolate shared networking state behind actors.
- Keep request/response boundaries typed with `Decodable` models.
- Model transport failures explicitly and deterministically.

## Transport and Retry

- Use URLSession async methods (`data(for:)`, `upload(for:)`, `download(for:)`).
- Apply bounded retries only to transient failures.
- Enforce exponential backoff and cap retries at 3 attempts.
- Retry only for network transport errors and 5xx responses.

## Reachability and Offline Uploads

- Use `NWPathMonitor` for connectivity-change signals.
- Keep an offline upload queue persisted to disk as JSON.
- Trigger queue drain only when path status transitions to satisfied.

## Security and Trust

- Enforce certificate pinning through `URLSessionDelegate`.
- Validate trust challenge for `exhibita.dineshd.dev`.
- Reject pinning omissions as architecture violations.

## Logging and Observability

- Use `OSLog` `Logger(subsystem:category:)`.
- For this project contract, restrict network logging to DEBUG builds.
- Forbid `print` and `debugPrint`.

## Error Model

`APIError` must include:

- `networkError(URLError)`
- `serverError(statusCode: Int, body: Data)`
- `decodingError(DecodingError)`
- `unauthorized`
- `notFound`

## Typing and URL Construction

- Build paths from enums, not raw URL strings.
- Keep `Request` protocol typed with `associatedtype Response: Decodable`.
- Ban dynamic model decoding patterns (`AnyCodable`, dynamic keys, `[String: Any]`).
