// Clear Authentication Data Script
// Run this in the browser console to clear any existing authentication tokens

console.log('🧹 Clearing authentication data...');

// Clear all possible auth-related localStorage items
const authKeys = [
  'auth_token',
  'user_data', 
  'token',
  'user',
  'demo_token'
];

authKeys.forEach(key => {
  if (localStorage.getItem(key)) {
    console.log(`Removing ${key}:`, localStorage.getItem(key));
    localStorage.removeItem(key);
  }
});

// Clear sessionStorage as well
authKeys.forEach(key => {
  if (sessionStorage.getItem(key)) {
    console.log(`Removing ${key} from session:`, sessionStorage.getItem(key));
    sessionStorage.removeItem(key);
  }
});

console.log('✅ Authentication data cleared! Refresh the page to see the login form.');
console.log('Demo credentials:');
console.log('Admin: username=admin, password=admin123');
console.log('Analyst: username=analyst, password=analyst123');