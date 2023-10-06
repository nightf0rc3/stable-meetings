
// document.querySelectorAll('#ReiseloesungList > div.loading-indicator > div.reiseloesung-list-page__wrapper > div:nth-child(2) > ul > li.verbindung-list__result-item.verbindung-list__result-item--1 > div > div.reiseloesung__item > div.reiseplan.reiseloesung__reiseplan > div.reiseplan__uebersicht > div.reiseplan__infos')
//
//
// li_elements = document.querySelectorAll('#ReiseloesungList > div.loading-indicator > div.reiseloesung-list-page__wrapper > div:nth-child(2) > ul > li')
// const h3Element = document.createElement('h3');
// h3Element.textContent = 'Hallo';
// li_elements.forEach(element => {
//
//     element.appendChild(h3Element)
// })
//
// const requestData = {
//     origin: 'Hello',
//     destination: 'World',
//     granularity: '1'
// };

// fetch route for each entry
// get entries
// const fetchOptions = {
//     method: 'GET',
//     headers: {
//         'Content-Type': 'application/json',
//     },
//     body: JSON.stringify(requestData),
// };

// fetch("18.197.50.92:80/get_route/", fetchOptions) //TODO add url
// fetch("https://18.197.50.92:80/get_route/?origin=Köln%2C%20Germany&destination=Berlin%2C%20Germany")
//     .then(response => response.json())
//     .then(console.log(data));
// fetch("https://18.197.50.92:80/get_route/?origin=Köln%2C%20Germany&destination=Berlin%2C%20Germany")
//     .then(Response => console.log(Response));

function waitForElementToBeDefined(elementSelector, callback) {
    const interval = setInterval(function() {
        const targetElement = document.querySelector(elementSelector);

        if (targetElement !== null && typeof targetElement !== 'undefined') {
            // The element is defined. You can now execute your desired action.
            clearInterval(interval); // Stop the interval.
            callback(targetElement); // Execute the callback with the target element.
        }
    }, 100); // Check every 100 milliseconds for the element.
}

waitForElementToBeDefined('#ReiseloesungList > div.loading-indicator > div.reiseloesung-list-page__wrapper > div:nth-child(2) > ul > li', function(element) {
    li_elements = document.querySelectorAll('#ReiseloesungList > div.loading-indicator > div.reiseloesung-list-page__wrapper > div:nth-child(2) > ul > li')
    console.log(li_elements)
    console.log(li_elements.tagType)
    li_elements.forEach(element => {
        reiseplan_elements = element.querySelectorAll('[class*="reiseplan__infos"]')
        const button = document.createElement('button');
        button.textContent = 'click';
        //button.style.backgroundImage = chrome.runtime.getURL('/icons/signal-solid.svg''); // Replace 'icon.png' with your actual image filename

        button.addEventListener('click', function() {
            // Redirect to the specified URL when the button is clicked
            window.open('https://stable-meetings.nightf0rc3.de/demo', '_blank');
        });
        reiseplan_elements.forEach(element =>{
            console.log('reiseplan element: ', element)
            element.appendChild(button)
        })
    })});

// li_elements = document.querySelectorAll('#ReiseloesungList > div.loading-indicator > div.reiseloesung-list-page__wrapper > div:nth-child(2) > ul > li')
// console.log(li_elements)
// console.log(li_elements.tagType)
// li_elements.forEach(element => {
//     reiseplan_elements = element.querySelectorAll('[class*="reiseplan__infos"]')
//     const button = document.createElement('button');
//     button.textContent = 'Click Me';
//     button.addEventListener('click', function() {
//         // Redirect to the specified URL when the button is clicked
//         window.location.href = 'https://18.197.50.92:80/demo';
//     });
//     reiseplan_elements.forEach(element =>{
//         console.log('reiseplan element: ', element)
//         element.appendChild(button)
//     })
// })
