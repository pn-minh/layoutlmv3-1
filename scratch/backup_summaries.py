import json
import os
import sys

out_dir = sys.argv[1] if len(sys.argv) > 1 else "/content/layoutlmv3-1/layoutlmv3/logs"
os.makedirs(out_dir, exist_ok=True)

summaries = {
    "funsd-base-baseline_3seed_summary.json": {
        "dataset": "funsd", "variant": "base", "mode": "baseline",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.899704, "eval_recall": 0.910500, "eval_f1": 0.905070, "eval_accuracy": 0.846348, "eval_loss": 1.129695},
            "123": {"eval_precision": 0.878168, "eval_recall": 0.901000, "eval_f1": 0.889437, "eval_accuracy": 0.821314, "eval_loss": 1.316718},
            "1993": {"eval_precision": 0.901795, "eval_recall": 0.904500, "eval_f1": 0.903145, "eval_accuracy": 0.841066, "eval_loss": 1.338800}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.893222, "std": 0.013098},
            "eval_recall": {"mean": 0.905333, "std": 0.004803},
            "eval_f1": {"mean": 0.899217, "std": 0.008544},
            "eval_accuracy": {"mean": 0.836243, "std": 0.013217},
            "eval_loss": {"mean": 1.261738, "std": 0.114945}
        }
    },
    "cord-base-baseline_3seed_summary.json": {
        "dataset": "cord", "variant": "base", "mode": "baseline",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.967251, "eval_recall": 0.970206, "eval_f1": 0.968726, "eval_accuracy": 0.974109, "eval_loss": 0.216924},
            "123": {"eval_precision": 0.967300, "eval_recall": 0.971734, "eval_f1": 0.969512, "eval_accuracy": 0.976231, "eval_loss": 0.191252},
            "1993": {"eval_precision": 0.960516, "eval_recall": 0.966387, "eval_f1": 0.963442, "eval_accuracy": 0.964346, "eval_loss": 0.237013}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.965022, "std": 0.003903},
            "eval_recall": {"mean": 0.969442, "std": 0.002758},
            "eval_f1": {"mean": 0.967227, "std": 0.003303},
            "eval_accuracy": {"mean": 0.971562, "std": 0.006346},
            "eval_loss": {"mean": 0.215063, "std": 0.022933}
        }
    },
    "funsd-base-full_3seed_summary.json": {
        "dataset": "funsd", "variant": "base", "mode": "full",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.918797, "eval_recall": 0.916500, "eval_f1": 0.917647, "eval_accuracy": 0.852435, "eval_loss": 1.219814},
            "123": {"eval_precision": 0.917925, "eval_recall": 0.911500, "eval_f1": 0.914701, "eval_accuracy": 0.815916, "eval_loss": 1.633083},
            "1993": {"eval_precision": 0.917967, "eval_recall": 0.912000, "eval_f1": 0.914974, "eval_accuracy": 0.828663, "eval_loss": 1.500647}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.918230, "std": 0.000491},
            "eval_recall": {"mean": 0.913333, "std": 0.002765},
            "eval_f1": {"mean": 0.915774, "std": 0.001625},
            "eval_accuracy": {"mean": 0.832338, "std": 0.018536},
            "eval_loss": {"mean": 1.451181, "std": 0.211028}
        }
    },
    "cord-base-full_3seed_summary.json": {
        "dataset": "cord", "variant": "base", "mode": "full",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.970252, "eval_recall": 0.971734, "eval_f1": 0.970992, "eval_accuracy": 0.968166, "eval_loss": 0.207698},
            "123": {"eval_precision": 0.964992, "eval_recall": 0.968678, "eval_f1": 0.966832, "eval_accuracy": 0.965195, "eval_loss": 0.216903},
            "1993": {"eval_precision": 0.968726, "eval_recall": 0.970206, "eval_f1": 0.969466, "eval_accuracy": 0.973260, "eval_loss": 0.217445}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.967990, "std": 0.002708},
            "eval_recall": {"mean": 0.970206, "std": 0.001528},
            "eval_f1": {"mean": 0.969097, "std": 0.002102},
            "eval_accuracy": {"mean": 0.968874, "std": 0.004079},
            "eval_loss": {"mean": 0.214015, "std": 0.005481}
        }
    },
    "funsd-base-no_boundary_3seed_summary.json": {
        "dataset": "funsd", "variant": "base", "mode": "no_boundary",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.919638, "eval_recall": 0.915500, "eval_f1": 0.917565, "eval_accuracy": 0.839573, "eval_loss": 1.366505},
            "123": {"eval_precision": 0.914414, "eval_recall": 0.913500, "eval_f1": 0.913957, "eval_accuracy": 0.822232, "eval_loss": 1.349019},
            "1993": {"eval_precision": 0.917417, "eval_recall": 0.916500, "eval_f1": 0.916958, "eval_accuracy": 0.825103, "eval_loss": 1.158295}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.917156, "std": 0.002621},
            "eval_recall": {"mean": 0.915167, "std": 0.001528},
            "eval_f1": {"mean": 0.916160, "std": 0.001928},
            "eval_accuracy": {"mean": 0.828969, "std": 0.009292},
            "eval_loss": {"mean": 1.291273, "std": 0.115509}
        }
    },
    "cord-base-no_boundary_3seed_summary.json": {
        "dataset": "cord", "variant": "base", "mode": "no_boundary",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.967963, "eval_recall": 0.969442, "eval_f1": 0.968702, "eval_accuracy": 0.971138, "eval_loss": 0.246410},
            "123": {"eval_precision": 0.970970, "eval_recall": 0.970970, "eval_f1": 0.970970, "eval_accuracy": 0.970289, "eval_loss": 0.219182},
            "1993": {"eval_precision": 0.971037, "eval_recall": 0.973262, "eval_f1": 0.972148, "eval_accuracy": 0.977504, "eval_loss": 0.194949}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.969990, "std": 0.001756},
            "eval_recall": {"mean": 0.971225, "std": 0.001921},
            "eval_f1": {"mean": 0.970607, "std": 0.001750},
            "eval_accuracy": {"mean": 0.972977, "std": 0.003943},
            "eval_loss": {"mean": 0.220180, "std": 0.025746}
        }
    },
    "funsd-base-no_segment_3seed_summary.json": {
        "dataset": "funsd", "variant": "base", "mode": "no_segment",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.890411, "eval_recall": 0.910000, "eval_f1": 0.900099, "eval_accuracy": 0.827400, "eval_loss": 1.257565},
            "123": {"eval_precision": 0.895020, "eval_recall": 0.916500, "eval_f1": 0.905632, "eval_accuracy": 0.838769, "eval_loss": 1.281979},
            "1993": {"eval_precision": 0.900892, "eval_recall": 0.909000, "eval_f1": 0.904928, "eval_accuracy": 0.828319, "eval_loss": 1.279675}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.895441, "std": 0.005252},
            "eval_recall": {"mean": 0.911833, "std": 0.004072},
            "eval_f1": {"mean": 0.903553, "std": 0.003023},
            "eval_accuracy": {"mean": 0.831496, "std": 0.006316},
            "eval_loss": {"mean": 1.273073, "std": 0.013485}
        }
    },
    "cord-base-no_segment_3seed_summary.json": {
        "dataset": "cord", "variant": "base", "mode": "no_segment",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.967275, "eval_recall": 0.970970, "eval_f1": 0.969119, "eval_accuracy": 0.973684, "eval_loss": 0.207652},
            "123": {"eval_precision": 0.966565, "eval_recall": 0.971734, "eval_f1": 0.969143, "eval_accuracy": 0.975806, "eval_loss": 0.212206},
            "1993": {"eval_precision": 0.954614, "eval_recall": 0.964095, "eval_f1": 0.959331, "eval_accuracy": 0.965620, "eval_loss": 0.238472}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.962818, "std": 0.007119},
            "eval_recall": {"mean": 0.968933, "std": 0.004218},
            "eval_f1": {"mean": 0.965864, "std": 0.005662},
            "eval_accuracy": {"mean": 0.971703, "std": 0.005393},
            "eval_loss": {"mean": 0.219443, "std": 0.016624}
        }
    },
    "funsd-base-no_hpe_3seed_summary.json": {
        "dataset": "funsd", "variant": "base", "mode": "no_hpe",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.917505, "eval_recall": 0.912000, "eval_f1": 0.914744, "eval_accuracy": 0.845889, "eval_loss": 1.334467},
            "123": {"eval_precision": 0.914172, "eval_recall": 0.916000, "eval_f1": 0.915085, "eval_accuracy": 0.831994, "eval_loss": 1.404697},
            "1993": {"eval_precision": 0.910866, "eval_recall": 0.909500, "eval_f1": 0.910183, "eval_accuracy": 0.816376, "eval_loss": 1.459901}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.914181, "std": 0.003320},
            "eval_recall": {"mean": 0.912500, "std": 0.003279},
            "eval_f1": {"mean": 0.913337, "std": 0.002737},
            "eval_accuracy": {"mean": 0.831420, "std": 0.014764},
            "eval_loss": {"mean": 1.399688, "std": 0.062862}
        }
    },
    "cord-base-no_hpe_3seed_summary.json": {
        "dataset": "cord", "variant": "base", "mode": "no_hpe",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.970970, "eval_recall": 0.970970, "eval_f1": 0.970970, "eval_accuracy": 0.974109, "eval_loss": 0.221378},
            "123": {"eval_precision": 0.971777, "eval_recall": 0.973262, "eval_f1": 0.972519, "eval_accuracy": 0.975806, "eval_loss": 0.192423},
            "1993": {"eval_precision": 0.968726, "eval_recall": 0.970206, "eval_f1": 0.969466, "eval_accuracy": 0.974533, "eval_loss": 0.218037}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.970491, "std": 0.001581},
            "eval_recall": {"mean": 0.971480, "std": 0.001590},
            "eval_f1": {"mean": 0.970985, "std": 0.001527},
            "eval_accuracy": {"mean": 0.974816, "std": 0.000884},
            "eval_loss": {"mean": 0.210613, "std": 0.015841}
        }
    },
    "funsd-large-baseline_3seed_summary.json": {
        "dataset": "funsd", "variant": "large", "mode": "baseline",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.914385, "eval_recall": 0.918500, "eval_f1": 0.916438, "eval_accuracy": 0.851975, "eval_loss": 1.506879},
            "123": {"eval_precision": 0.895355, "eval_recall": 0.915500, "eval_f1": 0.905315, "eval_accuracy": 0.837391, "eval_loss": 1.588325},
            "1993": {"eval_precision": 0.910891, "eval_recall": 0.920000, "eval_f1": 0.915423, "eval_accuracy": 0.850942, "eval_loss": 1.480555}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.906877, "std": 0.010131},
            "eval_recall": {"mean": 0.918000, "std": 0.002291},
            "eval_f1": {"mean": 0.912392, "std": 0.006150},
            "eval_accuracy": {"mean": 0.846769, "std": 0.008138},
            "eval_loss": {"mean": 1.525253, "std": 0.056186}
        }
    },
    "cord-large-baseline_3seed_summary.json": {
        "dataset": "cord", "variant": "large", "mode": "baseline",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.969559, "eval_recall": 0.973262, "eval_f1": 0.971407, "eval_accuracy": 0.977929, "eval_loss": 0.209308},
            "123": {"eval_precision": 0.966616, "eval_recall": 0.973262, "eval_f1": 0.969928, "eval_accuracy": 0.977504, "eval_loss": 0.200888},
            "1993": {"eval_precision": 0.972540, "eval_recall": 0.974026, "eval_f1": 0.973282, "eval_accuracy": 0.978778, "eval_loss": 0.209247}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.969572, "std": 0.002962},
            "eval_recall": {"mean": 0.973517, "std": 0.000441},
            "eval_f1": {"mean": 0.971539, "std": 0.001681},
            "eval_accuracy": {"mean": 0.978070, "std": 0.000648},
            "eval_loss": {"mean": 0.206481, "std": 0.004844}
        }
    },
    "funsd-large-full_3seed_summary.json": {
        "dataset": "funsd", "variant": "large", "mode": "full",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.917286, "eval_recall": 0.926000, "eval_f1": 0.921622, "eval_accuracy": 0.828089, "eval_loss": 1.315993},
            "123": {"eval_precision": 0.925463, "eval_recall": 0.925000, "eval_f1": 0.925231, "eval_accuracy": 0.847956, "eval_loss": 1.436600},
            "1993": {"eval_precision": 0.926537, "eval_recall": 0.927000, "eval_f1": 0.926768, "eval_accuracy": 0.850138, "eval_loss": 1.508250}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.923095, "std": 0.005060},
            "eval_recall": {"mean": 0.926000, "std": 0.001000},
            "eval_f1": {"mean": 0.924541, "std": 0.002642},
            "eval_accuracy": {"mean": 0.842061, "std": 0.012149},
            "eval_loss": {"mean": 1.420281, "std": 0.097162}
        }
    },
    "cord-large-full_3seed_summary.json": {
        "dataset": "cord", "variant": "large", "mode": "full",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.972540, "eval_recall": 0.974026, "eval_f1": 0.973282, "eval_accuracy": 0.976231, "eval_loss": 0.242330},
            "123": {"eval_precision": 0.972540, "eval_recall": 0.974026, "eval_f1": 0.973282, "eval_accuracy": 0.977080, "eval_loss": 0.207264},
            "1993": {"eval_precision": 0.973303, "eval_recall": 0.974790, "eval_f1": 0.974046, "eval_accuracy": 0.977080, "eval_loss": 0.214845}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.972794, "std": 0.000440},
            "eval_recall": {"mean": 0.974281, "std": 0.000441},
            "eval_f1": {"mean": 0.973537, "std": 0.000441},
            "eval_accuracy": {"mean": 0.976797, "std": 0.000490},
            "eval_loss": {"mean": 0.221480, "std": 0.018451}
        }
    },
    "funsd-large-no_boundary_3seed_summary.json": {
        "dataset": "funsd", "variant": "large", "mode": "no_boundary",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.920477, "eval_recall": 0.926000, "eval_f1": 0.923230, "eval_accuracy": 0.845544, "eval_loss": 1.458136},
            "123": {"eval_precision": 0.915591, "eval_recall": 0.922000, "eval_f1": 0.918784, "eval_accuracy": 0.841525, "eval_loss": 1.504203},
            "1993": {"eval_precision": 0.922923, "eval_recall": 0.922000, "eval_f1": 0.922461, "eval_accuracy": 0.836587, "eval_loss": 1.337305}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.919664, "std": 0.003733},
            "eval_recall": {"mean": 0.923333, "std": 0.002309},
            "eval_f1": {"mean": 0.921492, "std": 0.002376},
            "eval_accuracy": {"mean": 0.841219, "std": 0.004486},
            "eval_loss": {"mean": 1.433215, "std": 0.086195}
        }
    },
    "cord-large-no_boundary_3seed_summary.json": {
        "dataset": "cord", "variant": "large", "mode": "no_boundary",
        "seeds": [42, 123, 1993],
        "per_seed": {
            "42": {"eval_precision": 0.972540, "eval_recall": 0.974026, "eval_f1": 0.973282, "eval_accuracy": 0.977504, "eval_loss": 0.172858},
            "123": {"eval_precision": 0.971014, "eval_recall": 0.972498, "eval_f1": 0.971756, "eval_accuracy": 0.977080, "eval_loss": 0.180400},
            "1993": {"eval_precision": 0.963470, "eval_recall": 0.967150, "eval_f1": 0.965307, "eval_accuracy": 0.971986, "eval_loss": 0.191455}
        },
        "mean_std": {
            "eval_precision": {"mean": 0.969008, "std": 0.004856},
            "eval_recall": {"mean": 0.971225, "std": 0.003610},
            "eval_f1": {"mean": 0.970115, "std": 0.004233},
            "eval_accuracy": {"mean": 0.975523, "std": 0.003071},
            "eval_loss": {"mean": 0.181571, "std": 0.009354}
        },
        "metrics": {
            "eval_precision": {"values": [0.9725400457665904, 0.9710144927536232, 0.9634703196347032], "mean": 0.9690082860516389, "std": 0.004856298181246098, "mean_pct": 96.90, "std_pct": 0.49},
            "eval_recall": {"values": [0.974025974025974, 0.972498090145149, 0.9671504965622613], "mean": 0.9712248535777949, "std": 0.003610248759551269, "mean_pct": 97.12, "std_pct": 0.36},
            "eval_f1": {"values": [0.9732824427480916, 0.9717557251908397, 0.9653069004956157], "mean": 0.9701150228115157, "std": 0.004233349356998154, "mean_pct": 97.01, "std_pct": 0.42},
            "eval_accuracy": {"values": [0.9775042444821732, 0.9770797962648556, 0.9719864176570459], "mean": 0.9755234861346915, "std": 0.003070534014461043, "mean_pct": 97.55, "std_pct": 0.31},
            "eval_loss": {"values": [0.17285794019699097, 0.18039970099925995, 0.19145503640174866], "mean": 0.18157089253266653, "std": 0.009353703224830028, "mean_pct": 18.16, "std_pct": 0.94}
        }
    }
}

for fname, data in summaries.items():
    p = os.path.join(out_dir, fname)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
print(f"Successfully backed up {len(summaries)} summaries to {out_dir}")
