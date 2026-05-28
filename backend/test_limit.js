import fetch from 'node-fetch';

async function testSizeLimit() {
  // Create a 200kb dummy array
  const bigArray = new Array(5000).fill({ date: "2026-05-28", desc: "test transaction string for size testing", amount: 100.50 });
  
  const res = await fetch("http://localhost:5000/api/history", {
    method: "POST",
    headers: { "Content-Type": "application/json" }, // Missing auth, but we want to see if it fails on size first
    body: JSON.stringify({ transactions: bigArray })
  });
  
  console.log("Status:", res.status);
  const text = await res.text();
  console.log("Response:", text);
}
testSizeLimit();
