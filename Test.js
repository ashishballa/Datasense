//use let instead of var

//Reverse a string
function reverseString(str) {
    // Step 1. Use the split() method to return a new array
    let splitString = str.split(""); // let splitString = "hello".split("");

    // Step 2. Use the reverse() method to reverse the new created array
    let reverseArray = splitString.reverse(); // let     reverseArray = ["h", "e", "l", "l", "o"].reverse();
    
    // Step 3. Use the join() method to join all elements of the array into a string
    let joinArray = reverseArray.join(""); // let joinArray = ["o", "l", "l", "e", "h"].join("");

    //Step 4. Return the reversed string
    return joinArray; // return "olleh";
}

reverseString("hello");


//Check if a string is palindrome
function palindrome(str) {
    let re = /[\W_]/g;
    let lowRegStr = str.toLowerCase().replace(re, '');
    let reverseStr = lowRegStr.split('').reverse().join('');
    return reverseStr === lowRegStr;
}
