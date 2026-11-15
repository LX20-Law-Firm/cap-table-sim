"use strict";
const examples = {"holdings": {"Founder": "1000"}, "pre_money": "10000", "investment": "2000", "instruments": [{"holder": "SAFE holder", "principal": "1000", "cap": "5000", "discount": "0.2"}, {"holder": "Note holder", "principal": "1000", "discount": "0.2", "annual_interest": "0.1", "years": "2", "kind": "note"}], "pool_target": "0.2", "pool_timing": "pre", "quantum": null, "investor": "Round investor", "unit": "SPA shares"};
document.getElementById("calculator").addEventListener("submit", event => {
  event.preventDefault();
  const output = document.getElementById("output");
  try {
    const inputs = JSON.parse(document.getElementById("inputs").value);
    const result = CapTable.calculate(inputs);
    output.textContent = JSON.stringify(result, null, 2);
  } catch (error) { output.textContent = "Error: " + error.message; }
});
