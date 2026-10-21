import type { Analysis } from "../../../shared/api/contracts";
export const categories: Record<Analysis["issue_category"], string> = {
  out_of_stock: "Out of stock",
  stock_discrepancy: "Inventory discrepancy",
  competitor_pricing: "Competitor pricing",
  product_safety: "Product safety",
  commercial_request: "Commercial request",
  prompt_injection_attempt: "Instruction override",
  other: "General update",
};
export const actions: Record<
  Analysis["recommended_next_action"],
  { title: string; description: string }
> = {
  request_restock: {
    title: "Request replenishment",
    description:
      "System-recorded stock is zero. Ask the supply team to confirm availability and arrange replenishment.",
  },
  verify_stock_physically: {
    title: "Verify stock at the outlet",
    description:
      "The report and inventory record disagree. Ask the rep to check shelf and backroom stock before requesting replenishment.",
  },
  escalate_to_quality_team: {
    title: "Escalate to the quality team",
    description:
      "Route the report to the responsible quality team promptly. Preserve the reported details; a human must assess the safety concern.",
  },
  route_to_pricing_manager: {
    title: "Route to the pricing manager",
    description:
      "Collect supporting details for an authorized review. No price change, refund, or discount has been approved.",
  },
  request_more_info: {
    title: "Clarify the field report",
    description:
      "Collect the missing details below before making a business decision.",
  },
  flag_for_security_review: {
    title: "Review the instruction override",
    description:
      "The update contains an attempt to control the analysis. Review the original report and confirm the genuine business issue.",
  },
  no_action_needed: {
    title: "No action needed",
    description:
      "No issue requiring action was found. For stock reports, this can also mean the reported condition agrees with the system record.",
  },
};
