document.getElementById("shorten-btn").addEventListener("click", async function() {
    let longURL = document.getElementById("long_url").value;

    let response = await fetch("/shorten/", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({long_url: longURL})
    });

    let data = await response.json();
    if (data.short_url === undefined) {
        document.getElementById("short_url").innerHTML = `Enter full URL (with http:// or https://)`;
    } else {
        document.getElementById("short_url").innerHTML = `Short URL: <a href="${data.short_url}" target="_blank">${data.short_url}</a>`;
    }
})