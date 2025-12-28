const token = localStorage.getItem("token");

if (!token) {
    alert("Please login again");
    window.location.href = "login.html";
}

async function loadDashboard() {
    try {
        const res = await fetch("https://lunea-aoc1.onrender.com/api/dashboard/", {
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!res.ok) {
            alert("Session expired. Please login again.");
            localStorage.removeItem("token");
            window.location.href = "login.html";
            return;
        }

        const data = await res.json();

        // Populate dashboard
        document.getElementById("studentName").textContent = data.name || "-";
        document.getElementById("studentYear").textContent = data.year || "-";
        document.getElementById("studentBranch").textContent = (data.branch || "-").toUpperCase();
        document.getElementById("studentDept").textContent = data.department || "-";

        // Render subjects
        const subjectsEl = document.getElementById("subjectsList");
        if (subjectsEl) {
            subjectsEl.innerHTML = data.subjects?.map(s => `<li>${s.name}</li>`).join("") || "<li>No subjects</li>";
        }

        // Render exams
        const examsEl = document.getElementById("examsList");
        if (examsEl) {
            examsEl.innerHTML = data.exams?.map(e => `<li>${e.subject} - ${e.date}</li>`).join("") || "<li>No exams</li>";
        }

    } catch (err) {
        console.error(err);
        alert("Error connecting to server");
        localStorage.removeItem("token");
        window.location.href = "login.html";
    }
}

window.onload = loadDashboard;

function logout() {
    localStorage.removeItem("token");
    window.location.href = "login.html";
}
