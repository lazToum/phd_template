"use strict";
function ready(then) {
    if (typeof document === 'undefined') {
        // not in browser, node?
        then();
        return
    }
    if (['interactive', 'complete'].includes(document.readyState)) {
        then();
    } else {
        document.addEventListener('DOMContentLoaded', then);
    }
}
function helloWorld(){
    const msg = 'Hello World!';
    if (typeof alert !== 'undefined') {
        alert(msg);
    } else {
        console.log(msg);
    }
}
ready(helloWorld);
