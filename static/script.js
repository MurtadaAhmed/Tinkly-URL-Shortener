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
    let shortUrlContainer = document.getElementById("short_url");

    shortUrlContainer.className = "short-url-container";

    if (data.short_url === undefined) {
        shortUrlContainer.innerHTML = `<p class="error-message">Enter full URL (with http:// or https://)</p>`;
    } else {
        shortUrlContainer.innerHTML = `<p>Short URL:</p> 
                                        <a href="${data.short_url}" target="_blank">${data.short_url}</a>`;
    }
}
