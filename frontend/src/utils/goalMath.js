// Client-side mirror of a couple of small formulas from the backend's
// advisory/finance.py — used for the interactive "what-if" slider on the Goal
// detail view so it can respond instantly without a network round-trip per
// slider tick. The canonical numbers (recommended SIP, scenarios) still come
// from POST /goal-plan.
export function monthsToReachTarget(target, currentProgress, monthlySip, annualRate, maxMonths = 720) {
  if (currentProgress >= target) return 0;
  const monthlyRate = annualRate / 12;
  let balance = currentProgress;
  let months = 0;
  while (balance < target && months < maxMonths) {
    balance = balance * (1 + monthlyRate) + monthlySip;
    months++;
  }
  return months >= maxMonths ? null : months;
}

export const GOAL_ICONS = {
  Retirement: "🏖️",
  "Child Education": "🎓",
  "Home Purchase": "🏠",
  "Emergency Fund": "🚨",
  "Wealth Growth": "📈",
  Vacation: "✈️",
  Wedding: "💍",
};

export function goalStatus(recommendedMonthlySip, monthlyIncome) {
  if (!monthlyIncome) return "yellow";
  const ratio = recommendedMonthlySip / monthlyIncome;
  if (ratio <= 0.1) return "green";
  if (ratio <= 0.22) return "yellow";
  return "red";
}
