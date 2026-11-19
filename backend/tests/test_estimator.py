import pytest
from app.estimator import estimator_engine
from app.models import QueueEstimateRequest

def test_estimator_turnaround_prediction_monotonicity():
    """Higher page count and longer queues must logically produce higher turnaround times."""
    t_small, info_small = estimator_engine.predict_turnaround(page_count=5, is_color=False, needs_lamination=False, current_queue=0)
    t_large, info_large = estimator_engine.predict_turnaround(page_count=50, is_color=False, needs_lamination=False, current_queue=0)
    assert t_large > t_small, f"Expected 50 pages ({t_large}m) > 5 pages ({t_small}m)"

    t_empty_q, _ = estimator_engine.predict_turnaround(page_count=10, is_color=False, needs_lamination=False, current_queue=0)
    t_busy_q, _ = estimator_engine.predict_turnaround(page_count=10, is_color=False, needs_lamination=False, current_queue=4)
    assert t_busy_q > t_empty_q, f"Expected busy queue ({t_busy_q}m) > empty queue ({t_empty_q}m)"

def test_estimator_color_and_lamination_overhead():
    """Color printing and lamination must add turnaround time."""
    t_bw, _ = estimator_engine.predict_turnaround(page_count=10, is_color=False, needs_lamination=False, current_queue=1)
    t_color, _ = estimator_engine.predict_turnaround(page_count=10, is_color=True, needs_lamination=False, current_queue=1)
    t_lam, _ = estimator_engine.predict_turnaround(page_count=10, is_color=False, needs_lamination=True, current_queue=1)

    assert t_color > t_bw
    assert t_lam > t_bw

def test_pricing_calculation():
    """Verify fair billing calculation with sheet rates, lamination, and rush buffer."""
    # 10 pages B/W without lamination, 0 queue
    req_bw = QueueEstimateRequest(page_count=10, is_color=False, needs_lamination=False, current_queue_customers=0)
    p_bw = estimator_engine.calculate_pricing(req_bw, estimated_wait_minutes=2.5)
    assert p_bw.printing_fee == 20.0  # 10 * 2
    assert p_bw.lamination_fee == 0.0
    assert p_bw.total_fee == 20.0

    # 10 pages Color with lamination, 3 queue customers
    req_color = QueueEstimateRequest(page_count=10, is_color=True, needs_lamination=True, current_queue_customers=3)
    p_color = estimator_engine.calculate_pricing(req_color, estimated_wait_minutes=18.0)
    assert p_color.printing_fee == 100.0  # 10 * 10
    assert p_color.lamination_fee == 20.0 # 20
    assert p_color.rush_buffer > 0.0      # 3 * 2 + 5 (since wait > 15m) = 11.0
    assert p_color.total_fee == 100.0 + 20.0 + 11.0
