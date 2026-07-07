import { useEffect, useState } from "react";
import PageHeader from "../components/PageHeader";
import GoalCard from "../components/GoalCard";
import GoalDetailModal from "../components/GoalDetailModal";
import AddGoalModal from "../components/AddGoalModal";
import { LoadingBlock, ErrorBlock } from "../components/StateViews";
import { useCustomer } from "../context/CustomerContext";
import { api } from "../api/client";
import useFetch from "../hooks/useFetch";
import { goalStatus } from "../utils/goalMath";
import "./Goals.css";

export default function Goals() {
  const { customerId } = useCustomer();
  const { data: portfolio, loading: pLoading, error: pError } = useFetch(() => api.portfolio(customerId), [customerId]);
  const { data: insights } = useFetch(() => api.insights(customerId), [customerId]);

  const [plans, setPlans] = useState({});
  const [selectedGoalIdx, setSelectedGoalIdx] = useState(null);
  const [showAddGoal, setShowAddGoal] = useState(false);

  useEffect(() => {
    if (!portfolio) return;
    let cancelled = false;
    setPlans({});
    portfolio.goals.forEach((goal, idx) => {
      api
        .goalPlan({
          customer_id: customerId,
          goal_type: goal.type,
          target_amount: goal.target_amount,
          target_date: goal.target_date,
          current_progress: goal.current_progress,
        })
        .then((plan) => {
          if (!cancelled) setPlans((prev) => ({ ...prev, [idx]: plan }));
        })
        .catch(() => {});
    });
    return () => {
      cancelled = true;
    };
  }, [portfolio, customerId]);

  if (pLoading) {
    return (
      <>
        <PageHeader title="Goal Planner" subtitle="Track and plan your financial goals" />
        <div className="grid-2">
          <LoadingBlock height={180} />
          <LoadingBlock height={180} />
        </div>
      </>
    );
  }
  if (pError) {
    return (
      <>
        <PageHeader title="Goal Planner" subtitle="Track and plan your financial goals" />
        <ErrorBlock message={pError.message} />
      </>
    );
  }

  const monthlyIncome = insights?.avg_monthly_income;

  return (
    <>
      <PageHeader title="Goal Planner" subtitle={`${portfolio.goals.length} active goals`} />

      <div className="grid-2" style={{ marginTop: 12 }}>
        {portfolio.goals.map((goal, idx) => {
          const plan = plans[idx];
          const status = plan ? goalStatus(plan.recommended_monthly_sip, monthlyIncome) : null;
          return (
            <GoalCard
              key={idx}
              goal={goal}
              plan={plan}
              status={status}
              onClick={() => plan && setSelectedGoalIdx(idx)}
            />
          );
        })}

        <button className="card card-hover add-goal-card" onClick={() => setShowAddGoal(true)}>
          <span className="add-goal-icon">＋</span>
          <span>Add New Goal</span>
        </button>
      </div>

      {selectedGoalIdx !== null && plans[selectedGoalIdx] && (
        <GoalDetailModal
          goal={portfolio.goals[selectedGoalIdx]}
          plan={plans[selectedGoalIdx]}
          onClose={() => setSelectedGoalIdx(null)}
        />
      )}

      {showAddGoal && <AddGoalModal onClose={() => setShowAddGoal(false)} />}
    </>
  );
}
