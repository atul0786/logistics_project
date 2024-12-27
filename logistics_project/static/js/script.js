document.addEventListener('DOMContentLoaded', () => {
    console.log("Script loaded successfully!");

    // Get form elements
    const freightInput = document.getElementById('freight');
    const docketChargeInput = document.getElementById('docketCharge');
    const doorDeliveryInput = document.getElementById('doorDelivery');
    const handlingInput = document.getElementById('handling');
    const pickupInput = document.getElementById('pickup');
    const totalInput = document.getElementById('total');
    const grandTotalInput = document.getElementById('grandTotal');

    // Function to calculate total
    function calculateTotal() {
        console.log("Calculating total...");
        
        const freight = parseFloat(freightInput.value) || 0;
        const docketCharge = parseFloat(docketChargeInput.value) || 0;
        const doorDelivery = parseFloat(doorDeliveryInput.value) || 0;
        const handling = parseFloat(handlingInput.value) || 0;
        const pickup = parseFloat(pickupInput.value) || 0;

        console.log("Freight:", freight);
        console.log("Docket Charge:", docketCharge);
        console.log("Door Delivery:", doorDelivery);
        console.log("Handling:", handling);
        console.log("Pickup:", pickup);

        const total = freight + docketCharge + doorDelivery + handling + pickup;
        console.log("Total Calculated:", total);

        // Update the total and grand total fields
        totalInput.value = total.toFixed(2);
        grandTotalInput.value = total.toFixed(2);
    }

    // Attach event listeners to input fields to recalculate total when they change
    freightInput.addEventListener('input', calculateTotal);
    docketChargeInput.addEventListener('input', calculateTotal);
    doorDeliveryInput.addEventListener('input', calculateTotal);
    handlingInput.addEventListener('input', calculateTotal);
    pickupInput.addEventListener('input', calculateTotal);

    // Calculate total on page load
    calculateTotal();
});
