document.getElementById("shorten-btn").addEventListener("click", shortenUrl);
document.getElementById("long_url").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        shortenUrl();
    }
});

async function shortenUrl() {
    let longURL = document.getElementById("long_url").value;

    let response = await fetch("/shorten/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ long_url: longURL })
    });

    let data = await response.json();
    let error = document.getElementById("error");
    let shortUrl = document.getElementById("short-url");


    if (data.short_url === undefined) {
        error.innerHTML = `<p class="error-message">Enter full URL (with http:// or https://)</p>`;
    } else {
        shortUrl.value = `${data.short_url}`;
    }
}
