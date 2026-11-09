document.addEventListener("DOMContentLoaded", () => {
  const createBtn = document.getElementById("createBtn");
  const joinDiv = document.getElementById("join");
  const gameDiv = document.getElementById("game");

  const revealBtn = document.getElementById("reveal");
  const resetBtn = document.getElementById("reset");

  let revealed = false;

  // Check URL for /rooms/<uuid>
  const pathMatch = window.location.pathname.match(/^\/rooms\/([0-9a-f-]+)$/);
  if (pathMatch) {
    const roomId = pathMatch[1];
    joinRoom(roomId);
  }

  // Create room
  createBtn.onclick = async () => {
    const res = await fetch("/rooms", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: null })
    });
    const data = await res.json();
    window.location.href = `/rooms/${data.room_id}`;
  };

  // Join existing room
  function joinRoom(roomId) {
    document.getElementById("home").style.display = "none";
    joinDiv.style.display = "none";
    gameDiv.style.display = "block";

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/rooms/ws/${roomId}`);
    let userId = localStorage.getItem("userId");
    let userName = localStorage.getItem("userName");
    if (!userId) {
      userId = crypto.randomUUID();
      localStorage.setItem("userId", userId);
    }
    if (!userName) {
      userName = `User-${userId.slice(0,4)}`;
      localStorage.setItem("userName", userName);
    }

    ws.onopen = () => {
      ws.send(JSON.stringify({ userId, userName }));
    };


    ws.onclose = async (event) => {
      if (event.code === 4000) {
        // Room doesn't exist → show create button
        document.getElementById("home").style.display = "block";
        document.getElementById("join").style.display = "none";
        document.getElementById("game").style.display = "none";

        const createBtn = document.getElementById("createBtn");
        createBtn.textContent = `Create Room "${roomId}"`;
        createBtn.onclick = async () => {
          const res = await fetch("/rooms", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: roomId })
          });
          const data = await res.json();
          window.location.href = `/rooms/${data.room_id}`;
        };
      }
    };
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      updateVotes(data.votes, data.revealed);
      revealed = data.revealed;
    };

    document.getElementById("setNameBtn").onclick = () => {
      const name = document.getElementById("userName").value.trim();
      ws.send(JSON.stringify({ action: "set_name", userId, name }));
      localStorage.setItem("userName", name);
    };

    document.querySelectorAll(".card").forEach((btn) => {
      btn.onclick = () => {
        if (!revealed) {
          ws.send(JSON.stringify({ action: "vote", value: btn.dataset.value }));
          
          document.querySelectorAll(".card[data-value]").forEach(c => {
            c.classList.toggle("selected", c === btn);
          })
        }
      };
    });

    document.getElementById("reveal").onclick = () =>  {
      if (!revealed) {
        ws.send(JSON.stringify({ action: "reveal_room" }));
      }
    };
    
    document.getElementById("reset").onclick = () => {
      if (revealed) {
        ws.send(JSON.stringify({ action: "reset_room" }));
      }
    };

    document.getElementById("resetUsers").onclick = () => {
      ws.send(JSON.stringify({ action: "reset_users" }));
      window.location.reload();
    };
  }


  function updateVotes(votes, revealed) {
    const area = document.getElementById("voteArea");
    area.innerHTML = "";

    for (const v of votes) {
      const row = document.createElement("div");
      row.className = "voteRow";

      const nameSpan = document.createElement("span");
      nameSpan.className = "voteName";
      nameSpan.textContent = v.name;

      const voteSpan = document.createElement("span");
      voteSpan.className = "voteValue";
      voteSpan.textContent = v.vote;

      row.appendChild(nameSpan);
      row.appendChild(voteSpan);
      area.appendChild(row);
    }
    // Show/hide buttons

    if (revealed) {
      document.querySelectorAll(".card[data-value]").forEach(c => {
        c.classList.toggle("selected", false);
      })
      document.getElementById("cards").classList.add("revealed")
    
      revealBtn.style.background = "#eee";
      resetBtn.style.background = "";
    } else {
      document.getElementById("cards").classList.remove("revealed")

      revealBtn.style.background = "";
      resetBtn.style.background = "#eee";
    }
  }
});
