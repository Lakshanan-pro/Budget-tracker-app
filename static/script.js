const form = document.getElementById('expenseForm');
const dateInput = document.getElementById('date');
const filterDate = document.getElementById('filterDate');
const expenseId = document.getElementById('expenseId');

if (!dateInput.value) dateInput.value = new Date().toISOString().slice(0, 10);

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const id = expenseId.value;
    const payload = {
        amount: Number(document.getElementById('amount').value),
        category: document.getElementById('category').value,
        date: dateInput.value,
        description: document.getElementById('description').value.trim()
    };

    const response = await fetch(id ? `/expenses/${id}` : '/expenses', {
        method: id ? 'PUT' : 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) return alert(data.message || 'Unable to save expense');

    resetForm();
    await loadExpenses();
});

document.getElementById('cancelBtn').addEventListener('click', resetForm);
filterDate.addEventListener('change', loadExpenses);

async function loadExpenses() {
    const response = await fetch('/expenses');
    if (response.status === 401) return;
    const expenses = await response.json();
    const selectedDate = filterDate.value;
    const visible = selectedDate ? expenses.filter(item => item.date === selectedDate) : expenses;
    const list = document.getElementById('expenseList');

    if (!visible.length) {
        list.innerHTML = '<tr><td colspan="5" class="empty">No expenses found.</td></tr>';
    } else {
        list.innerHTML = visible.map(item => `
            <tr>
                <td>${escapeHtml(item.date)}</td>
                <td><span class="badge">${escapeHtml(item.category)}</span></td>
                <td>${escapeHtml(item.description || '—')}</td>
                <td class="amount">₹${Number(item.amount).toFixed(2)}</td>
                <td class="actions">
                    <button class="small edit" onclick='startEdit(${JSON.stringify(item)})'>Edit</button>
                    <button class="small delete" onclick="deleteExpense(${item.id})">Delete</button>
                </td>
            </tr>`).join('');
    }
    updateSummary(expenses);
}

function updateSummary(expenses) {
    const total = expenses.reduce((sum, item) => sum + Number(item.amount), 0);
    const counts = {};
    expenses.forEach(item => counts[item.category] = (counts[item.category] || 0) + Number(item.amount));
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    document.getElementById('totalExpense').textContent = `₹${total.toFixed(2)}`;
    document.getElementById('expenseCount').textContent = expenses.length;
    document.getElementById('topCategory').textContent = top ? top[0] : '—';
}

window.startEdit = function(item) {
    expenseId.value = item.id;
    document.getElementById('amount').value = item.amount;
    document.getElementById('category').value = item.category;
    dateInput.value = item.date;
    document.getElementById('description').value = item.description || '';
    document.getElementById('formTitle').textContent = 'Edit Expense';
    document.getElementById('submitBtn').textContent = 'Update Expense';
    document.getElementById('cancelBtn').classList.remove('hidden');
    window.scrollTo({top: 0, behavior: 'smooth'});
};

window.deleteExpense = async function(id) {
    if (!confirm('Delete this expense?')) return;
    const response = await fetch(`/expenses/${id}`, {method: 'DELETE'});
    if (response.ok) await loadExpenses();
};

function resetForm() {
    form.reset();
    expenseId.value = '';
    dateInput.value = new Date().toISOString().slice(0, 10);
    document.getElementById('formTitle').textContent = 'Add Expense';
    document.getElementById('submitBtn').textContent = 'Add Expense';
    document.getElementById('cancelBtn').classList.add('hidden');
}

function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
}

loadExpenses();
