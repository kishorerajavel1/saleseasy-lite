import { z } from "zod";

/** Runtime validation and TypeScript types share a single boundary definition. */
export const analysisSchema = z
  .object({
    issue_category: z.enum([
      "out_of_stock",
      "stock_discrepancy",
      "competitor_pricing",
      "product_safety",
      "commercial_request",
      "prompt_injection_attempt",
      "other",
    ]),
    urgency: z.enum(["low", "medium", "high", "critical"]),
    evidence: z
      .array(
        z
          .object({
            source: z.enum(["field_update", "verified_table"]),
            reference: z.string().min(1),
            verified: z.boolean(),
          })
          .strict()
          .refine((e) => e.verified === (e.source === "verified_table")),
      )
      .min(1),
    recommended_next_action: z.enum([
      "request_restock",
      "verify_stock_physically",
      "escalate_to_quality_team",
      "route_to_pricing_manager",
      "request_more_info",
      "flag_for_security_review",
      "no_action_needed",
    ]),
    missing_information: z.array(z.string()),
    needs_human_review: z.boolean(),
    review_reason: z.string().nullable(),
  })
  .strict()
  .refine((value) =>
    value.needs_human_review
      ? Boolean(value.review_reason?.trim())
      : value.review_reason === null,
  );

export const healthSchema = z.object({
  status: z.literal("ok"),
  max_input_chars: z.number().int().positive(),
});
export const inventorySchema = z.array(
  z.object({
    id: z.string(),
    outlet: z.string(),
    sku: z.string(),
    system_stock: z.number().int().nonnegative(),
  }),
);

export type Analysis = z.infer<typeof analysisSchema>;
export type Health = z.infer<typeof healthSchema>;
export type InventoryRecord = z.infer<typeof inventorySchema>[number];
export type Result = {
  data: Analysis;
};
