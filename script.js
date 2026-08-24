function saveHomeName() {

    let homeName =
        document.getElementById("homeInput").value.trim();


    if (homeName === "") {

        return;

    }


    document.getElementById("displayHomeName").innerHTML =
        homeName;


    document.getElementById("homeInputSection").style.display =
        "none";


    document.getElementById("homeDisplaySection").style.display =
        "block";

}



function editHomeName() {

    document.getElementById("homeInputSection").style.display =
        "block";


    document.getElementById("homeDisplaySection").style.display =
        "none";

}



function triggerPanic() {

    fetch("/panic", {

        method: "POST"

    })

    .then(response => response.json())

    .then(data => {

        window.location.reload();

    })

    .catch(error => {

        console.error("Panic request failed:", error);

    });

}



function setMode(mode) {

    fetch("/set_mode", {

        method: "POST",

        headers: {

            "Content-Type": "application/json"

        },

        body: JSON.stringify({

            mode: mode

        })

    })

    .then(response => response.json())

    .then(data => {

        window.location.reload();

    })

    .catch(error => {

        console.error("Mode change failed:", error);

    });

}