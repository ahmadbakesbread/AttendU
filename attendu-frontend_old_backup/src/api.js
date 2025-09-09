const API_BASE_URL = 'http://127.0.0.1:5000';

// Asynchronous function to register a student using formData object which contains user input

export const registerStudent = async (formData) => {
    try {
        // Attempt to post formData to the student registration API endpoint
        const response = await fetch(`${API_BASE_URL}/students`, {
          method: 'POST',
          body: formData,
        });
    
        // If the response is not ok, throw an error to be caught below
        if (!response.ok) {
          throw new Error('Student registration failed');
        }
       
        // Parse and return the JSON response from the API
        return await response.json();
      } catch (error) {
        // Log any errors to the console
        console.error('Error during student registration:', error);
        throw error;
      }
};

// Similar functions for registering teachers and parents, and for user login
// Each function posts to a different API endpoint and handles responses accordingly

export const registerTeacher = async (formData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/teachers`, {
          method: 'POST',
          body: formData,
        });
    
        if (!response.ok) {
          throw new Error('Teacher registration failed');
        }
    
        return await response.json();
      } catch (error) {
        console.error('Error during teacher registration:', error);
        throw error;
      }
};

export const registerParent = async (formData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/parents`, {
          method: 'POST',
          body: formData,
        });
    
        if (!response.ok) {
          throw new Error('Teacher registration failed');
        }
    
        return await response.json();
      } catch (error) {
        console.error('Error during teacher registration:', error);
        throw error;
      }
};

export const login = async (json) => {
  try {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: json
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Error during login:', error);
    throw error;
  }
};




    



    