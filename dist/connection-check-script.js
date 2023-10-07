// ----------------- Functions ------------------

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



// ----------------- script loaded in website ------------------

waitForElementToBeDefined('#ReiseloesungList > div.loading-indicator > div.reiseloesung-list-page__wrapper > div:nth-child(2) > ul > li', function(element) {

    li_elements = document.querySelectorAll('#ReiseloesungList > div.loading-indicator > div.reiseloesung-list-page__wrapper > div:nth-child(2) > ul > li')

    // ----------------- get origin & destination ------------------
    li_element = li_elements[0]
    start = document.querySelectorAll('span.test-reise-beschreibung-start-value');
    const start_location = document.querySelectorAll('span.test-reise-beschreibung-start-value')[1].textContent;
    const end_location = document.querySelectorAll('span.test-reise-beschreibung-ziel-value')[1].textContent;
    console.log('START: ', start_location, 'END: ', end_location);


    // ----------------- insert Buttons to results -----------------
    li_elements.forEach(element => {
        reiseplan_elements = element.querySelectorAll('[class*="reiseplan__infos"]')
        const button = document.createElement('button');
        button.textContent = 'Check network coverage'
        button.style.backgroundColor = 'rgb(236, 0, 21)';          // Set the background color to red
        button.style.color = 'white';                 // Set the text color to white
        button.style.fontWeight = 'bold';             // Set the font weight to bold
        button.style.borderRadius = '4px';            // Make the corners rounded
        button.style.padding = '7px 20px';            // Adjust padding for appearance
        button.style.height = '40px';

        // TBD add image as button
        // const iconImg = document.createElement('img');
        // iconImg.src = chrome.runtime.getURL('signal-solid.svg');
        // button.appendChild(iconImg);

        // ----------------- on button click -----------------
        button.addEventListener('click', function() {
            // window.open('https://stable-meetings.nightf0rc3.de/demo', '_blank');
            window.open(`https://stable-meetings.nightf0rc3.de/getGeo?origin=${start_location}&destination=${end_location}`, '_blank');
        });
        reiseplan_elements.forEach(element =>{
            console.log('reiseplan element: ', element)
            element.appendChild(button)
        })
    })
    // --------------------------- END ---------------------------
});
