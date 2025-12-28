const token = localStorage.getItem("token");
if (!token) window.location.href = "login.html";

const api = "https://lunea-aoc1.onrender.com";

/* ---------- LOAD PROFILE ---------- */
async function loadProfile() {
    try {
        const res = await fetch(`${api}/api/profile/me/`, {
            headers: { Authorization: `Bearer ${token}` }
        });

        if (!res.ok) {
            alert("Session expired. Login again.");
            localStorage.removeItem("token");
            window.location.href = "login.html";
            return;
        }

        const data = await res.json().catch(() => ({}));

        // Header
        document.getElementById("studentName").textContent = data.name || "";
        document.getElementById("studentId").textContent = data.id || "";

        // Form fields
        document.getElementById("name").value = data.name || "";
        document.getElementById("mobile").value = data.mobile || "";
        document.getElementById("year").value = data.year || "1";
        document.getElementById("department").value = data.department || "";

        // Load branches
        const branchRes = await fetch(`${api}/api/branches/`);
        const branches = await branchRes.json().catch(() => []);

        const branchSelect = document.getElementById("branch");
        branchSelect.innerHTML = "";

        branches.forEach(b => {
            const opt = document.createElement("option");
            opt.value = b.id;
            opt.textContent = `${b.name} (${b.department})`;
            if (b.id === data.branch_id) opt.selected = true;
            branchSelect.appendChild(opt);
        });

    } catch (err) {
        console.error("Profile load error:", err);
    }
}

/* ---------- UPDATE DEPARTMENT ON BRANCH CHANGE ---------- */
document.getElementById("branch").addEventListener("change", async (e) => {
    try {
        const branchId = e.target.value;
        const res = await fetch(`${api}/api/branches/`);
        const branches = await res.json().catch(() => []);
        const selected = branches.find(b => b.id == branchId);
        document.getElementById("department").value = selected?.department || "";
    } catch (err) {
        console.error("Branch change error:", err);
    }
});

/* ---------- UPDATE PROFILE ---------- */
document.getElementById("profileForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
        name: document.getElementById("name").value,
        mobile: document.getElementById("mobile").value,
        year: document.getElementById("year").value,
        branch_id: document.getElementById("branch").value
    };

    try {
        const res = await fetch(`${api}/api/profile/me/`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            alert("Update failed");
            return;
        }

        alert("Profile updated successfully");
        loadProfile();
    } catch (err) {
        console.error("Profile update error:", err);
        alert("Error updating profile");
    }
});

/* ---------- INIT ---------- */
window.onload = loadProfile;
