/* Mini Prometheus pilot demonstrator: every visible word (ADR-0023).
 *
 * To add Hindi after the first owner conversation, fill `hi` with the same keys as `en`. Any key
 * left out falls back to English, and the language switch appears as soon as `hi` has a key.
 * This file holds text only. The reason-code and status keys below are labels for codes the CLI
 * printed (see snapshots/data.js); nothing here decides a verdict.
 */
window.MP_PILOT_STRINGS = {
  en: {
    "app.title": "Mini Prometheus",
    "app.subtitle": "Can this workshop make this part? A five-minute walk-through.",
    "banner.synthetic": "Example data only. No real workshop, customer or job appears on these screens.",
    "lang.switch": "हिन्दी",

    "nav.workshop": "Your workshop",
    "nav.job": "A job",
    "nav.check": "The check",
    "nav.limits": "What it does not know",

    "label.synthetic": "Example data",
    "label.declared": "Declared by the workshop · not independently verified",
    "label.actual": "Actual Mini Prometheus output on example data",
    "label.explanation": "Explanation",
    "label.limitation": "Limitation",

    "workshop.lead": "Mini Prometheus starts from what the workshop says about itself: its machines, what each one can do, the materials it works with, and how tight a tolerance each process can hold.",
    "workshop.machines": "Machines",
    "workshop.can": "Can do",
    "workshop.materials": "Materials it machines",
    "workshop.tolerance": "Tightest tolerance it holds",
    "workshop.notInHouse": "Not done in-house",
    "workshop.none": "Nothing declared",
    "workshop.fingerprint": "Declaration fingerprint",
    "workshop.fingerprintNote": "If any machine, material or tolerance changes, this fingerprint changes too, and old answers are not reused.",

    "cap.cap.saw": "Cutting stock (saw)",
    "cap.cap.mill": "Milling",
    "cap.cap.drill": "Drilling",
    "cap.cap.bench": "Deburring (bench)",
    "cap.cap.cmm": "Inspection",
    "cap.cap.lathe": "Turning (lathe)",

    "op.cut_stock": "Cut stock",
    "op.face_mill": "Face milling",
    "op.pocket_mill": "Pocket milling",
    "op.drill": "Drilling",
    "op.turn": "Turning",
    "op.deburr": "Deburring",
    "op.inspect": "Inspection",

    "stock.bar": "Bar",
    "stock.plate": "Plate",
    "stock.sheet": "Sheet",
    "stock.block": "Block",
    "stock.tube": "Tube",

    "case.bracket": "Aluminium bracket",
    "case.turned_shaft": "Turned steel shaft",
    "case.brass_cover": "Brass cover",
    "case.precision_plate": "Precision plate",

    "job.lead": "A job is described the way a customer would ask for it. Pick one of the example jobs.",
    "job.pick": "Example jobs",
    "job.material": "Material",
    "job.stock": "Starting stock",
    "job.quantity": "Quantity",
    "job.tolerance": "General tolerance",
    "job.operations": "Operations needed",
    "job.next": "See the check",

    "check.question": "Can this workshop make it?",
    "check.steps": "Which machine does each step",
    "check.operation": "Operation",
    "check.machine": "Machine",
    "check.noMachine": "No machine in this workshop for this step",
    "check.reasons": "Why",
    "check.meaningYes": "This means every step fits what the workshop declared. It does not promise the part will come out right first time.",
    "check.details": "Technical details",
    "check.command": "Command that produced this result",
    "check.output": "Exact output",
    "check.trace": "Result fingerprint",
    "check.plan": "Plan fingerprint",
    "check.declaration": "Workshop declaration fingerprint",

    "status.MANUFACTURABLE": "Yes, with this workshop's declared machines",
    "status.NOT_MANUFACTURABLE": "No, not with this workshop's declared machines",
    "status.PLAN_INVALID": "No. The order of operations breaks a rule the workshop declared",
    "status.INFRA_ERROR": "The check could not run",

    "tone.MANUFACTURABLE": "go",
    "tone.NOT_MANUFACTURABLE": "stop",
    "tone.PLAN_INVALID": "stop",
    "tone.INFRA_ERROR": "hold",

    "reason.CAPABILITY_MISSING": "One of the operations needs a capability the workshop does not have in-house.",
    "reason.MATERIAL_UNSUPPORTED": "The material is not on the workshop's material list.",
    "reason.TOLERANCE_UNSUPPORTED": "The job asks for a tighter tolerance than the workshop says its machines can hold.",
    "reason.PRECEDENCE_VIOLATION": "The operations are in an order the workshop said it never uses.",
    "reason.RESOURCE_UNAVAILABLE": "The machine this step needs is marked as unavailable.",
    "reason.PLAN_MALFORMED": "The job description itself is inconsistent.",

    "limits.lead": "Mini Prometheus is careful about what it does not know. These are its limits today.",
    "limits.drawings": "It does not read drawings or 3D models. It works only from the written job description.",
    "limits.size": "It does not know machine size limits, so it cannot say whether a part fits on a machine.",
    "limits.materials": "Materials are listed for the whole workshop. It does not know which machine can cut which material.",
    "limits.costTime": "It does not estimate cost, cycle time or delivery time.",
    "limits.live": "These screens show results captured in advance. Nothing is calculated on this screen.",
    "limits.example": "All of this is example data. No real workshop, customer or job is shown.",
    "limits.declared": "It trusts what the workshop declares. It does not inspect the machines itself.",
    "limits.next": "With your records, it would use your machines and your past jobs, and we would compare its answers with what really happened, including the jobs you turned down.",

    "footer.provenance": "Captured with Mini Prometheus at commit",
    "footer.generator": "Regenerate with",
    "footer.noData": "The result file (snapshots/data.js) is missing. Run demo/pilot/capture.py to create it."
  },
  hi: {}
};
