const category_names = {
  incoming_money: "Incoming Money",
  payments_to_code_holders: "Payments to Code Holders",
  transfers_to_mobile_numbers: "Transfer to Mobile Numbers",
  bank_deposits: "Bank Deposits",
  airtime_bill_payments: "Airtime Purchase",
  cash_power: "Cash Power",
  withdrawal: "Withdrawal",
  bank_transfer: "Bank Transfer",
  pack: "Internet and Voice Bundle Purchases",
  third_party: "Third Party",
  uncategorized: "No category",
};

let transactions = [];

const chartColors = {
  primaryColor: "#42b883",
  backgroundColor: "rgba(66, 184, 131, 0.1)",
  textColor: "#fff",
  gridColor: "rgba(255, 255, 255, 0.1)",
  colors: [
    "#42b883",
    "#ff6384",
    "#36a2eb",
    "#ffcd56",
    "#ff9f40",
    "#4bc0c0",
    "#9966ff",
    "#c9cbcf",
    "#ff9999",
    "#99ff99",
    "#99ccff",
  ],
};

function formatAmount(amount) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
  }).format(amount);
}

let volumeChart = null;
let distributionChart = null;
let volumeByTypeChart = null;
let paymentsVsDepositsChart = null;

function createInitialCharts() {
  const volumeCtx = document.getElementById("transactionVolume").getContext("2d");
  const distributionCtx = document.getElementById("transactionDistribution").getContext("2d");
  const volumeByTypeCtx = document.getElementById("volumeByType").getContext("2d");
  const paymentsVsDepositsCtx = document.getElementById("paymentsVsDeposits").getContext("2d");

  Chart.defaults.color = chartColors.textColor;
  Chart.defaults.borderColor = chartColors.gridColor;
  Chart.defaults.font.family = "'Inter', 'Helvetica', 'Arial', sans-serif";
  Chart.defaults.font.size = 13;

  volumeChart = new Chart(volumeCtx, {
    type: "line",
    data: { labels: [], datasets: [] },
    options: {},
  });

  distributionChart = new Chart(distributionCtx, {
    type: "doughnut",
    data: { labels: [], datasets: [] },
    options: {},
  });

  volumeByTypeChart = new Chart(volumeByTypeCtx, {
    type: "bar",
    data: { labels: [], datasets: [] },
    options: {},
  });

  paymentsVsDepositsChart = new Chart(paymentsVsDepositsCtx, {
    type: "pie",
    data: { labels: [], datasets: [] },
    options: {},
  });
}

async function fetchTransactions() {
  try {
    const response = await fetch("http://127.0.0.1:5000/transactions");
    transactions = await response.json();

    document.querySelector(".balance-amount").textContent = `${formatAmount(
      parseInt(transactions[0].total_transactions)
    )} RWF`;

    populateTransactionTable(transactions);
    updateCharts(transactions);
    populateTypeFilter();
  } catch (error) {
    console.error("Error fetching transactions:", error);
  }
}

function populateTransactionTable(data) {
  const tbody = document.querySelector(".transactions-table tbody");
  tbody.innerHTML = "";

  data.forEach((t) => {
    const amount = parseFloat(t.amount);
    const row = `
      <tr>
        <td>${t.readable_date}</td>
        <td>${category_names[t.category]}</td>
        <td class="${amount >= 0 ? "text-green-500" : "text-red-500"}">RWF ${formatAmount(Math.abs(amount))}</td>
        <td>RWF ${formatAmount(parseFloat(t.balance))}</td>
      </tr>`;
    tbody.insertAdjacentHTML("beforeend", row);
  });
}

function updateCharts(data) {
  const monthlyTotals = {};
  const typeVolumes = {};
  let deposits = 0;
  let payments = 0;

  data.forEach((t) => {
    const date = new Date(t.readable_date);
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    monthlyTotals[key] = (monthlyTotals[key] || 0) + Math.abs(parseFloat(t.amount));

    typeVolumes[t.category] = (typeVolumes[t.category] || 0) + Math.abs(parseFloat(t.amount));

    if (t.category === "incoming_money" || t.category === "bank_deposits") deposits += Math.abs(t.amount);
    else payments += Math.abs(t.amount);
  });

  const sortedMonths = Object.keys(monthlyTotals).sort();
  const labels = sortedMonths.map((k) => {
    const d = new Date(k);
    return d.toLocaleString("en-US", { month: "short", year: "numeric" });
  });

  volumeChart.data.labels = labels;
  volumeChart.data.datasets = [
    {
      label: "Monthly Transaction Volume (RWF)",
      data: sortedMonths.map((k) => monthlyTotals[k]),
      borderColor: chartColors.primaryColor,
      backgroundColor: chartColors.backgroundColor,
      fill: true,
      tension: 0.4,
      pointBackgroundColor: chartColors.primaryColor,
      pointBorderColor: "#fff",
    },
  ];
  volumeChart.update();

  const distLabels = Object.keys(typeVolumes).map((k) => category_names[k]);
  const distData = Object.values(typeVolumes);

  distributionChart.data.labels = distLabels;
  distributionChart.data.datasets = [
    {
      data: distData,
      backgroundColor: chartColors.colors,
      borderColor: "rgba(0, 0, 0, 0.1)",
      borderWidth: 2,
    },
  ];
  distributionChart.update();

  volumeByTypeChart.data.labels = distLabels;
  volumeByTypeChart.data.datasets = [
    {
      label: "Transaction Volume by Type",
      data: distData,
      backgroundColor: chartColors.colors,
      borderColor: "rgba(0, 0, 0, 0.1)",
    },
  ];
  volumeByTypeChart.update();

  paymentsVsDepositsChart.data.datasets = [
    {
      data: [deposits, payments],
      backgroundColor: [chartColors.colors[0], chartColors.colors[1]],
    },
  ];
  paymentsVsDepositsChart.update();
}

function populateTypeFilter() {
  const typeFilter = document.getElementById("type-filter");
  typeFilter.innerHTML = `<option value="">All Types</option>`;

  const types = new Set(transactions.map((t) => t.category));
  types.forEach((type) => {
    const option = document.createElement("option");
    option.value = type;
    option.textContent = category_names[type] || type;
    typeFilter.appendChild(option);
  });
}

function applyFilters() {
  const selectedType = document.getElementById("type-filter").value;
  const selectedDate = document.getElementById("date-filter").value;
  const searchValue = Number(document.getElementById("search").value);

  let filtered = [...transactions];

  if (selectedType) {
    filtered = filtered.filter((t) => t.category === selectedType);
  }

  if (selectedDate) {
    const d = new Date(selectedDate);
    d.setUTCHours(0, 0, 0, 0);
    filtered = filtered.filter((t) => new Date(t.readable_date).toDateString() === d.toDateString());
  }

  if (searchValue) {
    filtered = filtered.filter((t) => parseInt(t.amount) === searchValue);
  }

  populateTransactionTable(filtered);
  updateCharts(filtered);
}

// ✅ Event listeners
document.getElementById("date-filter").addEventListener("change", applyFilters);
document.getElementById("search").addEventListener("input", applyFilters);
document.getElementById("type-filter").addEventListener("change", applyFilters);

// ✅ Reset Filters Button Logic
document.getElementById("reset-filters").addEventListener("click", () => {
  document.getElementById("search").value = "";
  document.getElementById("type-filter").value = "";
  document.getElementById("date-filter").value = "";

  populateTransactionTable(transactions);
  updateCharts(transactions);
});

// ✅ Run setup
createInitialCharts();
fetchTransactions();
