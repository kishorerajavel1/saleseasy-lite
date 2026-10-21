# Observed live-model iteration

On 21 October 2026, the first Groq evaluation using `openai/gpt-oss-20b` and prompt `2026-10-21.1` passed six of seven cases. The missing-information input “Stock is low at one of the stores” was classified as `out_of_stock`; its requested action and questions were otherwise correct.

Prompt `2026-10-21.2` explicitly distinguishes low stock from unavailable, out-of-stock, and zero-unit claims. The immediate rerun classified the same input as `other`, selected `request_more_info`, and requested both outlet and SKU. Rapid unpaced calls later reached the free-tier quota and were recorded as provider failures, so the final repeat evaluation uses the documented 15-second interval.
