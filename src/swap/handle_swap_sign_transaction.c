#include "handle_swap_sign_transaction.h"
#include "ux.h"
#include "os.h"
#include "os_io_seproxyhal.h"
#include "global.h"
#include "swap_lib_calls.h"
#include "swap_utils.h"

#ifdef HAVE_NBGL
#include "nbgl_use_case.h"
#endif

// Save the BSS address where we will write the return value when finished
static uint8_t* G_swap_sign_return_value_address;

bool copy_transaction_parameters(create_transaction_parameters_t* params) {
    // first copy parameters to stack, and then to global data.
    // We need this "trick" as the input data position can overlap with btc-app globals
    swapStrings_t stack_data;
    memset(&stack_data, 0, sizeof(stack_data));
    strncpy(stack_data.address, params->destination_address, sizeof(stack_data.address) - 1);
    strncpy(stack_data.destination_tag,
            params->destination_address_extra_id,
            sizeof(stack_data.destination_tag));
    if ((stack_data.address[sizeof(stack_data.address) - 1] != '\0') ||
        (stack_data.destination_tag[sizeof(stack_data.destination_tag) - 1] != '\0')) {
        return false;
    }

    if (!swap_str_to_u64(params->amount, params->amount_length, &stack_data.amount)) {
        return false;
    }

    if (!swap_str_to_u64(params->fee_amount, params->fee_amount_length, &stack_data.fee)) {
        return false;
    }

    // Full reset the global variables
    os_explicit_zero_BSS_segment();
    // Keep the address at which we'll reply the signing status
    G_swap_sign_return_value_address = &params->result;
    // Commit the values read from exchange to the clean global space
    memcpy(&approval_strings.swap, &stack_data, sizeof(stack_data));

    return true;
}

void __attribute__((noreturn)) finalize_exchange_sign_transaction(bool is_success) {
    *G_swap_sign_return_value_address = is_success;
    os_lib_end();
}

void handle_swap_sign_transaction(void) {
    called_from_swap = true;
    reset_transaction_context();
    io_seproxyhal_init();
    UX_INIT();
#ifdef HAVE_NBGL
    nbgl_useCaseSpinner("Signing");
#endif  // HAVE_BAGL
    USB_power(0);
    USB_power(1);
    // ui_idle();
    PRINTF("USB power ON/OFF\n");
#ifdef TARGET_NANOX
    // grab the current plane mode setting
    G_io_app.plane_mode = os_setting_get(OS_SETTING_PLANEMODE, NULL, 0);
#endif  // TARGET_NANOX
#ifdef HAVE_BLE
    BLE_power(0, NULL);
    BLE_power(1, NULL);
#endif  // HAVE_BLE
    app_main();
}
