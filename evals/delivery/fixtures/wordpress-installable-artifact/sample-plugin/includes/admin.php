<?php

if (!defined('ABSPATH')) {
    exit;
}

function sample_plugin_register_settings(): void {
    // Add the sample_label setting here.
}
add_action('admin_init', 'sample_plugin_register_settings');

function sample_plugin_render_label_field(): void {
    echo '<input type="text" name="sample_label" value="" />';
}
