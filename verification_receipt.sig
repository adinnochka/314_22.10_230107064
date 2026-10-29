{
  "student_id": "230107064",
  "generated_at_utc": "2026-10-29T08:00:17.316597+00:00",
  "status": "FAIL",
  "checks": [
    {
      "status": "PASS",
      "name": "M0",
      "message": "Host profile exists; N=1024, seed=34278"
    },
    {
      "status": "PASS",
      "name": "M1 files",
      "message": "Stride and dense-kernel datasets are present"
    },
    {
      "status": "FAIL",
      "name": "M1 loop interchange",
      "message": "D:\\Downloads\\314_29.10\\CS482_Lab\\results\\loop_interchange.json"
    },
    {
      "status": "WARN",
      "name": "M1 numerical verification",
      "message": "Presence of result files does not prove that i-j-k and i-k-j outputs agree within 1e-12. The actual arrays or a reproducible comparison are required."
    },
    {
      "status": "PASS",
      "name": "M2 metrics",
      "message": "Unpadded/padded rows and formulas verified"
    },
    {
      "status": "WARN",
      "name": "M2 counter verification",
      "message": "TSV data does not include every final counter value or the privatized implementation. Exact P*K correctness cannot be independently verified from the saved results."
    },
    {
      "status": "PASS",
      "name": "M3 metrics",
      "message": "Strong/weak dimensions, formulas and arithmetic intensity verified"
    },
    {
      "status": "WARN",
      "name": "M3 roofline",
      "message": "Hardware peak bandwidth or compute ceiling is missing; bound classification is not established"
    },
    {
      "status": "WARN",
      "name": "M3 numerical verification",
      "message": "Saved checksums are finite, but independent single-thread reference arrays are needed for full numerical verification."
    }
  ],
  "file_sha256": {
    "host_profile.json": "7c14f22cdfaa4d130caacc56f84185da71421fb5661dbf1afbf737632965edd0",
    "salted_params.json": "c05918ed538fcc6aa943e6c57a5d5b3919e1ac8e4ee0de6fc2d481b3161d55ed",
    "stride_results.tsv": "d351fb05a95c2ecd10fa392a6a45c1307eeb4ae7da41ad39075ff6cfbdc9c883",
    "dense_kernel_results.json": "37fccb610c3a7173995a6c9decd5f31d0419509f09b13d9fd0f523792118f143",
    "false_sharing_karp_flatt.tsv": "cc065af62a1f3a8ec179ba754c1082e1db5f31757261c86afb15bc66030b01ad",
    "scaling_metrics.tsv": "dba9cda9e2a82166369f505d3fdfdf923c2b1063ece28d60e1382b839b56da63",
    "roofline_summary.json": "4fca185d995e48d983c9bd1085e7f11a78d1bcbabb4d991ca4b164b85152b07a"
  },
  "note": "Local integrity receipt, not the official course verification signature. File hashes cover raw file bytes, not salted rounded numerical arrays.",
  "receipt_sha256": "62bd72972e27c45c8c8cec68ced58569c77ddc8074d9ac064575d073ba92fa3e"
}