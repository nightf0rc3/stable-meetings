// http://18.197.50.92/demo?origin=K%C3%B6ln%2C%20Germany&destination=Berlin%2C%20Germany%22

const baseUrl = 'http://18.197.50.92/demo'; // Replace with your base URL
const params = {
  origin: 'Köln',
  destination: 'Berlin'
};

const url = new URL(baseUrl);
Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));

fetch(url)
  .then(response => {
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.text(); // Parse the response as text
  })
  .then(data => {
    // Handle the data from the response
    console.log('Response data:', data);
  })
  .catch(error => {
    // Handle errors
    console.error('Error:', error);
  });