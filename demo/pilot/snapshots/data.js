window.MP_PILOT_DATA = {
  "cases": [
    {
      "command": "python -m mini_prometheus.orchestration.runner demo/pilot/inputs/job_bracket.json --capability-model-file demo/pilot/inputs/shop.example_workshop.json",
      "episode_hash": "sha256:a1d4125a512ae90be8058ee6303daedf140d8c63b3581326dce1bbac457c7368",
      "exit_code": 0,
      "id": "bracket",
      "job_path": "demo/pilot/inputs/job_bracket.json",
      "job_sha256": "13bea0805d2db3289eecdfb76e4cba06af9986feeaef8d99856d240624865751",
      "plan_hash": "sha256:00ebf85fc37790e2bf011018fc2e5ed603060f55953fd98fec219e61275c95e2",
      "plan_path": "demo/pilot/snapshots/case.bracket.plan.json",
      "plan_sha256": "5105631d1556a8a71fdcebb82287b899a6f6c3f3425f2ecc78cc7a59444be29a",
      "reason_codes": [],
      "request": {
        "declared_operations": [
          {
            "op": "cut_stock"
          },
          {
            "op": "face_mill",
            "target": "top_face"
          },
          {
            "op": "drill",
            "target": "mount_hole_1"
          },
          {
            "op": "drill",
            "target": "mount_hole_2"
          },
          {
            "op": "deburr"
          },
          {
            "op": "inspect"
          }
        ],
        "material": "Aluminum 6061",
        "quantity": 25,
        "request_id": "d0000000-0000-4000-8000-000000000001",
        "schema_version": "1.0.0",
        "stock_form": "block",
        "tolerances": {
          "general_tolerance_mm": 0.1
        }
      },
      "shop_declaration_hash": "sha256:77f39940f9a613a34b025bb045e0cda326165a1c44f72e61f54f2d342ef33a07",
      "status": "MANUFACTURABLE",
      "stdout": "MANUFACTURABLE [] plan sha256:00ebf85fc37790e2bf011018fc2e5ed603060f55953fd98fec219e61275c95e2 episode sha256:a1d4125a512ae90be8058ee6303daedf140d8c63b3581326dce1bbac457c7368 shop model \"Example workshop (synthetic)\" sha256:77f39940f9a613a34b025bb045e0cda326165a1c44f72e61f54f2d342ef33a07 (synthetic, declared by Mini Prometheus pilot demonstrator (synthetic example) on 2026-11-07; not independently verified) trace sha256:de8dd311142127776f11837ee91641c58ff564f1dd137136a0bea57483025b87 -> <temporary episode store>\n",
      "stdout_path": "demo/pilot/snapshots/case.bracket.stdout.txt",
      "stdout_sha256": "da8463427a11b51b8d0adad8d6ddbfe35f057797675224a9a979e92a7b302d20",
      "steps": [
        {
          "index": 0,
          "op": "cut_stock",
          "required_capability": "cap.saw",
          "resource_id": "saw01"
        },
        {
          "index": 1,
          "op": "face_mill",
          "required_capability": "cap.mill",
          "resource_id": "mill01"
        },
        {
          "index": 2,
          "op": "drill",
          "required_capability": "cap.drill",
          "resource_id": "mill01"
        },
        {
          "index": 3,
          "op": "drill",
          "required_capability": "cap.drill",
          "resource_id": "mill01"
        },
        {
          "index": 4,
          "op": "deburr",
          "required_capability": "cap.bench",
          "resource_id": "bench01"
        },
        {
          "index": 5,
          "op": "inspect",
          "required_capability": "cap.cmm",
          "resource_id": "cmm01"
        }
      ],
      "trace_hash": "sha256:de8dd311142127776f11837ee91641c58ff564f1dd137136a0bea57483025b87"
    },
    {
      "command": "python -m mini_prometheus.orchestration.runner demo/pilot/inputs/job_turned_shaft.json --capability-model-file demo/pilot/inputs/shop.example_workshop.json",
      "episode_hash": "sha256:666ab3d5ad9b19b9a09439e36ec8ab46694d6382da407a8aa784e9deee47b44e",
      "exit_code": 0,
      "id": "turned_shaft",
      "job_path": "demo/pilot/inputs/job_turned_shaft.json",
      "job_sha256": "0e48f97cb8b5dd8a3dac2ecb69e5803d378f6fd9cd71f9db496cecaa91b6aefb",
      "plan_hash": "sha256:1344dd455ad1cbc07c161eb3fd6bd77d206d88d0e03aeae40effd291f31692c4",
      "plan_path": "demo/pilot/snapshots/case.turned_shaft.plan.json",
      "plan_sha256": "d664fd143dd7fb3dbbc2293731c86b0fd07265919f8c1b76018d11723c71aaa2",
      "reason_codes": [
        "CAPABILITY_MISSING"
      ],
      "request": {
        "declared_operations": [
          {
            "op": "cut_stock"
          },
          {
            "op": "turn",
            "target": "outer_diameter"
          },
          {
            "op": "deburr"
          },
          {
            "op": "inspect"
          }
        ],
        "material": "Steel 1018",
        "quantity": 40,
        "request_id": "d0000000-0000-4000-8000-000000000002",
        "schema_version": "1.0.0",
        "stock_form": "bar",
        "tolerances": {
          "general_tolerance_mm": 0.1
        }
      },
      "shop_declaration_hash": "sha256:77f39940f9a613a34b025bb045e0cda326165a1c44f72e61f54f2d342ef33a07",
      "status": "NOT_MANUFACTURABLE",
      "stdout": "NOT_MANUFACTURABLE [CAPABILITY_MISSING] plan sha256:1344dd455ad1cbc07c161eb3fd6bd77d206d88d0e03aeae40effd291f31692c4 episode sha256:666ab3d5ad9b19b9a09439e36ec8ab46694d6382da407a8aa784e9deee47b44e shop model \"Example workshop (synthetic)\" sha256:77f39940f9a613a34b025bb045e0cda326165a1c44f72e61f54f2d342ef33a07 (synthetic, declared by Mini Prometheus pilot demonstrator (synthetic example) on 2026-11-07; not independently verified) trace sha256:a2ad8b3e3ccb2a5d5426af08e74a1c756377d4df4b6e69588797256aa006e62a -> <temporary episode store>\n",
      "stdout_path": "demo/pilot/snapshots/case.turned_shaft.stdout.txt",
      "stdout_sha256": "65634e250e0ff1fe4c468b2f629460126a23a0804c22acf4eb03794a81c39dfe",
      "steps": [
        {
          "index": 0,
          "op": "cut_stock",
          "required_capability": "cap.saw",
          "resource_id": "saw01"
        },
        {
          "index": 1,
          "op": "turn",
          "required_capability": "UNSUPPORTED_OP:turn",
          "resource_id": null
        },
        {
          "index": 2,
          "op": "deburr",
          "required_capability": "cap.bench",
          "resource_id": "bench01"
        },
        {
          "index": 3,
          "op": "inspect",
          "required_capability": "cap.cmm",
          "resource_id": "cmm01"
        }
      ],
      "trace_hash": "sha256:a2ad8b3e3ccb2a5d5426af08e74a1c756377d4df4b6e69588797256aa006e62a"
    },
    {
      "command": "python -m mini_prometheus.orchestration.runner demo/pilot/inputs/job_brass_cover.json --capability-model-file demo/pilot/inputs/shop.example_workshop.json",
      "episode_hash": "sha256:e9d94e1979c9c2244edf16390f518339f731897352dff545da14c0241f532064",
      "exit_code": 0,
      "id": "brass_cover",
      "job_path": "demo/pilot/inputs/job_brass_cover.json",
      "job_sha256": "f717698c302786bf94501a86eb248be6cce79daf092095e07367c15ea1b95294",
      "plan_hash": "sha256:a0f9e8eed1de96186c02648eb776fd325ae5467b40d6e3b40049f41b4ffd2636",
      "plan_path": "demo/pilot/snapshots/case.brass_cover.plan.json",
      "plan_sha256": "8e2d46450d3fd1f524f7f83fdf41fe4c962378593a936c4b005d696d64195848",
      "reason_codes": [
        "MATERIAL_UNSUPPORTED"
      ],
      "request": {
        "declared_operations": [
          {
            "op": "cut_stock"
          },
          {
            "op": "face_mill",
            "target": "top_face"
          },
          {
            "op": "drill",
            "target": "centre_hole"
          },
          {
            "op": "deburr"
          },
          {
            "op": "inspect"
          }
        ],
        "material": "Brass 360",
        "quantity": 10,
        "request_id": "d0000000-0000-4000-8000-000000000003",
        "schema_version": "1.0.0",
        "stock_form": "block",
        "tolerances": {
          "general_tolerance_mm": 0.1
        }
      },
      "shop_declaration_hash": "sha256:77f39940f9a613a34b025bb045e0cda326165a1c44f72e61f54f2d342ef33a07",
      "status": "NOT_MANUFACTURABLE",
      "stdout": "NOT_MANUFACTURABLE [MATERIAL_UNSUPPORTED] plan sha256:a0f9e8eed1de96186c02648eb776fd325ae5467b40d6e3b40049f41b4ffd2636 episode sha256:e9d94e1979c9c2244edf16390f518339f731897352dff545da14c0241f532064 shop model \"Example workshop (synthetic)\" sha256:77f39940f9a613a34b025bb045e0cda326165a1c44f72e61f54f2d342ef33a07 (synthetic, declared by Mini Prometheus pilot demonstrator (synthetic example) on 2026-11-07; not independently verified) trace sha256:ce632914d89d5aafdaa96e9e3e97bdddd19f1b45dcbf66479146f5e94d9c2cb0 -> <temporary episode store>\n",
      "stdout_path": "demo/pilot/snapshots/case.brass_cover.stdout.txt",
      "stdout_sha256": "1d2c12451c63631ded2e16e5e1e97ca1c99fc70b97ee5b19335d7e7ab9568dbd",
      "steps": [
        {
          "index": 0,
          "op": "cut_stock",
          "required_capability": "cap.saw",
          "resource_id": "saw01"
        },
        {
          "index": 1,
          "op": "face_mill",
          "required_capability": "cap.mill",
          "resource_id": "mill01"
        },
        {
          "index": 2,
          "op": "drill",
          "required_capability": "cap.drill",
          "resource_id": "mill01"
        },
        {
          "index": 3,
          "op": "deburr",
          "required_capability": "cap.bench",
          "resource_id": "bench01"
        },
        {
          "index": 4,
          "op": "inspect",
          "required_capability": "cap.cmm",
          "resource_id": "cmm01"
        }
      ],
      "trace_hash": "sha256:ce632914d89d5aafdaa96e9e3e97bdddd19f1b45dcbf66479146f5e94d9c2cb0"
    },
    {
      "command": "python -m mini_prometheus.orchestration.runner demo/pilot/inputs/job_precision_plate.json --capability-model-file demo/pilot/inputs/shop.example_workshop.json",
      "episode_hash": "sha256:b4ccc107a79530dea1a432328c9ba516181fbbf365d94692c02f8c0aafce5b10",
      "exit_code": 0,
      "id": "precision_plate",
      "job_path": "demo/pilot/inputs/job_precision_plate.json",
      "job_sha256": "945d7bb2d69eddf3c161d2c80e375f9bd36d132b2ff802022420691f759adf20",
      "plan_hash": "sha256:47fed9ea227a66a23ce3c2f3ad5ef5f47fe04a8f51bdc241376e163d9a596f9e",
      "plan_path": "demo/pilot/snapshots/case.precision_plate.plan.json",
      "plan_sha256": "8d112e8cec7f618e39d3868629997a3d54e3ec60974241c879482ce2dd9f5144",
      "reason_codes": [
        "TOLERANCE_UNSUPPORTED"
      ],
      "request": {
        "declared_operations": [
          {
            "op": "cut_stock"
          },
          {
            "op": "face_mill",
            "target": "top_face"
          },
          {
            "op": "pocket_mill",
            "target": "pocket_1"
          },
          {
            "op": "inspect"
          }
        ],
        "material": "Aluminum 6061",
        "quantity": 5,
        "request_id": "d0000000-0000-4000-8000-000000000004",
        "schema_version": "1.0.0",
        "stock_form": "plate",
        "tolerances": {
          "general_tolerance_mm": 0.01
        }
      },
      "shop_declaration_hash": "sha256:77f39940f9a613a34b025bb045e0cda326165a1c44f72e61f54f2d342ef33a07",
      "status": "NOT_MANUFACTURABLE",
      "stdout": "NOT_MANUFACTURABLE [TOLERANCE_UNSUPPORTED] plan sha256:47fed9ea227a66a23ce3c2f3ad5ef5f47fe04a8f51bdc241376e163d9a596f9e episode sha256:b4ccc107a79530dea1a432328c9ba516181fbbf365d94692c02f8c0aafce5b10 shop model \"Example workshop (synthetic)\" sha256:77f39940f9a613a34b025bb045e0cda326165a1c44f72e61f54f2d342ef33a07 (synthetic, declared by Mini Prometheus pilot demonstrator (synthetic example) on 2026-11-07; not independently verified) trace sha256:08f9d58a1d893f8e47682fc22b32484dfece20350e269ea17dc01509a6fac3df -> <temporary episode store>\n",
      "stdout_path": "demo/pilot/snapshots/case.precision_plate.stdout.txt",
      "stdout_sha256": "947abb296a0b755467637f2505eda6372b89c3a8095185cf9aa84be84a65b3e8",
      "steps": [
        {
          "index": 0,
          "op": "cut_stock",
          "required_capability": "cap.saw",
          "resource_id": "saw01"
        },
        {
          "index": 1,
          "op": "face_mill",
          "required_capability": "cap.mill",
          "resource_id": "mill01"
        },
        {
          "index": 2,
          "op": "pocket_mill",
          "required_capability": "cap.mill",
          "resource_id": "mill01"
        },
        {
          "index": 3,
          "op": "inspect",
          "required_capability": "cap.cmm",
          "resource_id": "cmm01"
        }
      ],
      "trace_hash": "sha256:08f9d58a1d893f8e47682fc22b32484dfece20350e269ea17dc01509a6fac3df"
    }
  ],
  "meta": {
    "adr": "ADR-0023",
    "evidence": "synthetic example data; verdicts are actual MP-S1 CLI output on it",
    "generator": "demo/pilot/capture.py",
    "mp_commit": "f0206082693967466b6d3dc442ae2587c50486f3"
  },
  "shop": {
    "document": {
      "capability_tolerance_mm": {
        "cap.drill": 0.05,
        "cap.mill": 0.02
      },
      "declaration": {
        "declared_by": "Mini Prometheus pilot demonstrator (synthetic example)",
        "declared_on": "2026-11-07",
        "sources": []
      },
      "display_name": "Example workshop (synthetic)",
      "evidence_class": "synthetic",
      "model_version": "1.0.0",
      "notes": "Synthetic example for the shop-owner pilot demonstrator (ADR-0023). It describes no real workshop. Derived from tests/fixtures/shop_models/three_cell_synthetic.json, with tolerance minimums added.",
      "op_capability": {
        "cut_stock": "cap.saw",
        "deburr": "cap.bench",
        "drill": "cap.drill",
        "face_mill": "cap.mill",
        "inspect": "cap.cmm",
        "pocket_mill": "cap.mill"
      },
      "resources": [
        {
          "capabilities": [
            "cap.mill",
            "cap.drill"
          ],
          "resource_id": "mill01"
        },
        {
          "capabilities": [
            "cap.mill"
          ],
          "resource_id": "mill02"
        },
        {
          "capabilities": [
            "cap.saw"
          ],
          "resource_id": "saw01"
        },
        {
          "capabilities": [
            "cap.bench"
          ],
          "resource_id": "bench01"
        },
        {
          "capabilities": [
            "cap.cmm"
          ],
          "resource_id": "cmm01"
        }
      ],
      "schema_version": "1.0.0",
      "supported_materials": [
        "aluminum 6061",
        "steel 1018"
      ],
      "unsupported_ops": [
        "turn"
      ]
    },
    "evidence_class": "synthetic",
    "path": "demo/pilot/inputs/shop.example_workshop.json",
    "sha256": "966f741459c406f14d17694b767c42979fdd4e2f8f28057b419557eefb3dbde4",
    "shop_content_hash": "sha256:8e0b9895bd79d2e85fa423d34b4b0b74e754142e3422858e0b172224510b5b59",
    "shop_declaration_hash": "sha256:77f39940f9a613a34b025bb045e0cda326165a1c44f72e61f54f2d342ef33a07"
  }
};
