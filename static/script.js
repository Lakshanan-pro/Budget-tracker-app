document.getElementById("transactionForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const data = {
        type: document.getElementById("type").value,
        amount: parseFloat(document.getElementById("amount").value),
        category: document.getElementById("category").value,
        description: document.getElementById("description").value,
        date: document.getElementById("date").value,
    };

    await fetch("/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });

    e.target.reset();
    fetchTransactions();
});

async function fetchTransactions() {
    const date = document.getElementById("filterDate").value;
    const res = await fetch("/transactions" + (date ? `?date=${date}` : ""));
    const data = await res.json();

    document.getElementById("totalIncome").textContent = data.income;
    document.getElementById("totalExpense").textContent = data.expense;
    document.getElementById("balance").textContent = data.balance;

    const list = document.getElementById("transactionList");
    list.innerHTML = "";

    data.transactions.forEach(tx => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${tx.type}</td>
            <td>₹${tx.amount}</td>
            <td>${tx.category}</td>
            <td>${tx.description}</td>
            <td>${tx.date}</td>
            <td><button onclick="deleteTransaction(${tx.id})">Delete</button></td>
        `;
        list.appendChild(row);
    });
}

async function deleteTransaction(id) {
    await fetch(`/delete/${id}`, { method: "DELETE" });
    fetchTransactions();
}

window.onload = fetchTransactions;
