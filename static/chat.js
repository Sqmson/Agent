window.addEventListener('load', async () => {
        try {
            const res = await fetch("/initial");
            const data = await res.json();

            const h3 = document.querySelector(".empty-state h3");
            const p = document.querySelector(".empty-state p");

            h3.textContent = "🤖 " + data.reply.split("\n")[0];
            p.textContent = data.reply.split("\n").slice(1).join(" ");

            if (data.suggestions) {
                const wrap = document.createElement("div");
                wrap.className = "suggestion-buttons";
                data.suggestions.forEach(item => {
                    const btn = document.createElement("button");
                    btn.textContent = item;
                    btn.onclick = () => {
                        const input = document.querySelector(".chatbox__footer input");
                        input.value = item;
                        document.querySelector(".send__button").click();
                    };
                    wrap.appendChild(btn);
                });
                document.querySelector(".empty-state").appendChild(wrap);
            }
        } catch (err) {
            console.error("Greeting fetch error:", err);
        }
    });