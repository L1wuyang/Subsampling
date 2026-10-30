"""Recheck compact scalar tail witnesses, without raw data or native trajectories.

Requires mpmath==1.3.0. Binary64 values are stored as exact hexadecimal strings.
"""
import argparse
import hashlib
import json
from pathlib import Path
import mpmath as mp


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def exact(value, context=mp.mp):
    return context.mpf(float.fromhex(value))


def residual(method, x, count, context):
    if method == "Landweber":
        return (1 - x) ** count
    if method == "Showalter":
        return (1 - x + x*x/2 - x*x*x/6 + x*x*x*x/24) ** count
    previous, current = context.mpf(1), 1 - x
    # Nesterov with omega=1; use alternating-sign magnitudes on this witness.
    if not bool(x > 1):
        raise ValueError("The Nesterov witness requires h*lambda>1")
    previous, current = context.mpf(1), x - 1
    for j in range(2, count + 1):
        momentum = context.mpf(j - 2) / j
        previous, current = current, (x - 1) * ((1 + momentum)*current + momentum*previous)
    return (-1) ** count * current


def calculate(witness, data, context):
    row = data["rows"][str(witness["index_zero_based"])]
    s = sum((exact(value, context)**2 for value in row["coordinates_hex"]), context.mpf(0))
    response = exact(row["response_hex"], context)
    if witness["probability_convention"] == "binary64":
        probability = exact(witness["probability_hex"], context)
    else:
        probability = context.mpf(1) / data["training_rows"]
    x = exact(witness["step_hex"], context) * s / probability
    r = residual(witness["method"], x, witness["steps"], context)
    estimator_norm = abs(response) / context.sqrt(s) * abs(1 - r)
    if not bool(estimator_norm > 8):
        raise ValueError("Norm-8 witness premise is not met")
    log_error = 2 * context.log(estimator_norm / 8 - 1) / context.log(10)
    return x, log_error, {str(n): n * context.log(probability) / context.log(10) + log_error
                          for n in data["budgets"]}


def verify(input_path):
    data = read(input_path)
    mp.mp.dps = 80
    mp.iv.dps = 60
    target = data["landweber_target_hex"]
    target_norm = mp.iv.sqrt(sum((exact(v, mp.iv)**2 for v in target), mp.iv.mpf(0)))
    if not bool(target_norm.b < 8):
        raise ValueError("Restored Landweber target norm is not below 8")
    for method in ["Landweber", "Showalter", "Nesterov"]:
        if not 0 < data["historical_target_norm_squared"][method] < 64:
            raise ValueError("Historical summary does not support norm-8 premise")
    checks = []
    for witness in data["witnesses"]:
        x, log_error, bounds = calculate(witness, data, mp.mp)
        _, _, intervals = calculate(witness, data, mp.iv)
        for n, expected in witness["reference_log10_bounds"].items():
            if abs(bounds[n] - mp.mpf(expected)) > mp.mpf("1e-6"):
                raise ValueError("Witness disagrees with archived calculation")
        integer_bound = int(mp.floor(bounds["50000"])) - 1
        if not bool(intervals["50000"].a > integer_bound):
            raise ValueError("Interval check does not prove integer lower bound")
        checks.append({"method": witness["method"], "rule": witness["rule"],
                       "index_zero_based": witness["index_zero_based"],
                       "probability_convention": witness["probability_convention"],
                       "h_lambda": mp.nstr(x, 78),
                       "log10_relative_error_lower_bound_norm8": mp.nstr(log_error, 78),
                       "log10_MSE_lower_bounds": {n: mp.nstr(v, 78) for n, v in bounds.items()},
                       "N50000_interval": str(intervals["50000"]),
                       "N50000_conservative_integer_exponent": integer_bound,
                       "interval_proves_integer_bound": True})
    return {"schema_version": 1, "input_sha256": hashlib.sha256(Path(input_path).read_bytes()).hexdigest(),
            "decimal_precision": 80, "interval_decimal_precision": 60,
            "landweber_restored_target_norm_interval": str(target_norm), "checks": checks,
            "scope": data["scope"], "passed": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(__file__).with_name("witness_inputs.json"))
    parser.add_argument("--output", type=Path, help="Optional JSON report; omit to print to stdout")
    args = parser.parse_args()
    result = verify(args.input)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(json.dumps({"passed": True, "witnesses": len(result["checks"])}))
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
