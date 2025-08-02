document.getElementById('transactionForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        type: document.getElementById('type').value,
        amount: parseFloat(document.getElementById('amount').value),
        category: document.getElementById('category').value,
        description: document.getElementById('description').value,
        date: document.getElementById('date').value,
    };

    const res = await fetch('/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (res.ok) {
        fetchTransactions();
        document.getElementById('transactionForm').reset();
    } else {
        alert("Failed to add transaction");
    }
});

async function fetchTransactions() {
    const res = await fetch('/transactions');
    const transactions = await res.json();
    const list = document.getElementById('transactionList');
    list.innerHTML = '';

    let income = 0, expense = 0;

    transactions.forEach(tx => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${tx.type}</td>
            <td>₹${tx.amount.toFixed(2)}</td>
            <td>${tx.category}</td>
            <td>${tx.description}</td>
            <td>${tx.date}</td>
            <td><button onclick="deleteTransaction(${tx.id})">Delete</button></td>
        `;
        list.appendChild(row);

        if (tx.type === 'Income') income += tx.amount;
        else expense += tx.amount;
    });

    document.getElementById('totalIncome').textContent = income.toFixed(2);
    document.getElementById('totalExpense').textContent = expense.toFixed(2);
    document.getElementById('balance').textContent = (income - expense).toFixed(2);
}

async function deleteTransaction(id) {
    const res = await fetch('/transactions', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
    });

    if (res.ok) fetchTransactions();
}

window.onload = fetchTransactions;
