"""Run the three grade-change demonstrations for feature generation."""

from prediction_feature_processor import PredictionFeatureProcessor


def raw(basis_weight: float, stock_flow: float = 150.0) -> dict:
    return {
        "stock_flow": stock_flow,
        "steam_pressure": 8.5,
        "machine_speed": 900.0,
        "moisture": 5.2,
        "basis_weight": basis_weight,
    }


SCENARIOS = {
    "Scenario A - Yellow Risk": [19.95 + minute * 0.05 for minute in range(6)],
    "Scenario B - Red Risk": [19.4 - minute * 0.12 for minute in range(6)],
    "Scenario C - Green Safe": [24.0, 24.005, 24.0, 24.005, 24.0, 24.005],
}


def main() -> None:
    for scenario, weights in SCENARIOS.items():
        processor = PredictionFeatureProcessor()
        for weight in weights:
            features = processor.process(raw(weight))
        print(f"\n{scenario}")
        print("-" * len(scenario))
        for name, value in features.items():
            print(f"{name:32} {value:10.4f}")
        print(f"XGBoost array shape: {processor.to_array(features).shape}")


if __name__ == "__main__":
    main()
