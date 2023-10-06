
const elements = document.querySelectorAll('[id*="section-directions-trip-"]');

// const iconUrl = chrome.runtime.getURL('/icons/4b74e5ea94181fde37324c605c8aa453--smiley-faces.jpg');

elements.forEach(element => {
    // const icon = document.createElement('img');
    // icon.src = iconUrl;
    // icon.style.width = '100px';
    // icon.style.height = '100px';
    // icon.style.top = '0';
    // icon.style.right = '0';
    // icon.style.zIndex = '9999'; // Ensures the icon is on top of other content
    // element.style.position = 'relative'; // Ensure the element's position is relative

    // Append the icon to the element
    // element.appendChild(icon);
    const h3Element = document.createElement('h3');
    h3Element.textContent = 'Hallo'; // Set the text content for the <h3> element

    element.appendChild(h3Element);
});



// const icon_good = document.createElement("img_good");
// const icon_ok = document.createElement("img_ok");
// const icon_bad = document.createElement("img_bad");
// const icon_good.src = chrome.extension.getURL("icon.png"); // Replace "icon.png" with the actual icon path
// const icon_ok.src = chrome.extension.getURL("icon.png"); // Replace "icon.png" with the actual icon path
// const icon_bad.src = chrome.extension.getURL("icon.png"); // Replace "icon.png" with the actual icon path
// var icon;
//
// const requestData = {
//     origin: 'Hello',
//     destination: 'World',
//     granularity: '1'
// };
//
// // fetch route for each entry
// // get entries
// const fetchOptions = {
//     method: 'GET',
//     headers: {
//         'Content-Type': 'application/json',
//     },
//     body: JSON.stringify(requestData),
// };
//
// fetch("https://www.mywebsite.com/my-api", fetchOptions) //TODO add url
//     .then(response => response.json())
//     .then(data => {
//         if (data === "good") {
//            icon = icon_good
//         }
//         else if(data == "ok"){
//             icon = icon_ok
//         }
//         else if(data == "bad"){
//             icon = icon_bad
//         }
//         else
//             icon = null
//     });
//
// // Append the icon to the target field
// targetField.appendChild(icon);