#!/usr/bin/env python3

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple
import json
import os

@dataclass
class DCDevice:
    """Represents devices on a single DC line"""
    dc_number: int
    smart_card: int = 0
    fingerprint: int = 0
    door_sensor: int = 0
    magnetic_lock: int = 0
    electric_lock: int = 0
    rex_button: int = 0
    push_button: int = 0
    break_glass: int = 0
    buzzer: int = 0
    double_door_lock: int = 0  # Counts as BOTH 1 input AND 1 output
    ddl_sensors: int = 0
    
    def calculate_totals(self):
        """Calculate readers, inputs, outputs for this DC line"""
        # Readers = Smart Card + Fingerprint (Excel Column M)
        readers = self.smart_card + self.fingerprint
        
        # Inputs = Door Sensor + REX Button + Push Button + Break Glass + Buzzer + Magnetic Lock + DDL Sensors + Double Door Lock
        # NOTE: Double Door Lock counts as 1 input
        inputs = (self.door_sensor + self.rex_button + self.push_button + 
                 self.break_glass + self.buzzer + self.magnetic_lock + 
                 self.ddl_sensors + self.double_door_lock)  # Add double_door_lock to inputs
        
        # Outputs = Magnetic Lock + Electric Lock + DDL Sensors + Double Door Lock
        # NOTE: Double Door Lock counts as 1 output
        outputs = (self.magnetic_lock + self.electric_lock + 
                  self.ddl_sensors + self.double_door_lock)  # Add double_door_lock to outputs
        
        return {'readers': readers, 'inputs': inputs, 'outputs': outputs}

class KantechDCCalculator:
    def __init__(self):
        self.dc_lines: List[DCDevice] = []
        
        # Controller models - selected ONLY based on readers
        self.controllers = [
            {'name': 'kt-1', 'readers': 1, 'cost': 450, 'inputs': 4, 'outputs': 2},
            {'name': 'kt-2', 'readers': 2, 'cost': 750, 'inputs': 8, 'outputs': 2},
            {'name': 'kt-400', 'readers': 4, 'cost': 1400, 'inputs': 16, 'outputs': 4}
        ]
        
        # All available expansion modules (from your Excel Sheet2)
        self.expansion_modules = [
            {'name': 'inout16 (16/0)', 'inputs': 16, 'outputs': 0, 'cost': 447},
            {'name': 'inout16 (12/4)', 'inputs': 12, 'outputs': 4, 'cost': 447},
            {'name': 'inout16 (8/8)', 'inputs': 8, 'outputs': 8, 'cost': 447},
            {'name': 'inout16 (4/12)', 'inputs': 4, 'outputs': 12, 'cost': 447},
            {'name': 'inout16 (0/16)', 'inputs': 0, 'outputs': 16, 'cost': 447},
            {'name': 'in16', 'inputs': 16, 'outputs': 0, 'cost': 470},
            {'name': 'r8', 'inputs': 0, 'outputs': 8, 'cost': 470}
        ]
        
        # License information - UPDATED with correct logic
        self.license_info = {
            'special': {
                'name': 'Kantech Special License',
                'max_controllers': 32,
                'description': 'For systems with 32 or fewer controllers (non-redundant)',
                'cost': 0  # License cost included in controller cost
            },
            'corporate': {
                'name': 'Kantech Corporate License',
                'min_controllers': 33,
                'description': 'For systems with more than 32 controllers (non-redundant)',
                'cost': 0  # License cost included in controller cost
            },
            'global': {
                'name': 'Global License',
                'description': 'Required for ANY redundancy configuration (replaces Special/Corporate)',
                'cost': 0  # Base license cost
            },
            'gateway': {
                'name': 'Gateway License',
                'description': 'Required for gateway/server communication in redundant systems',
                'cost': 500  # Example cost
            },
            'redundancy': {
                'name': 'Redundancy License',
                'description': 'Additional license for failover/redundancy capability',
                'cost': 750  # Example cost
            }
        }
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title):
        print("=" * 60)
        print(f"{title:^60}")
        print("=" * 60)
        print()
    
    def add_dc_line_interactive(self):
        """Interactive DC line addition"""
        self.clear_screen()
        self.print_header("ADD DC LINE CONFIGURATION")
        
        dc_number = len(self.dc_lines) + 1
        print(f"DC Line {dc_number}")
        print("-" * 40)
        
        dc_line = DCDevice(dc_number=dc_number)
        
        # Get device counts
        print("Enter number of devices for this DC line:")
        print()
        
        devices = [
            ("INDOOR Smart Card Reader", 'smart_card'),
            ("Finger Print Reader", 'fingerprint'),
            ("Door Sensor", 'door_sensor'),
            ("Magnetic Door Lock", 'magnetic_lock'),
            ("Electric Door Lock", 'electric_lock'),
            ("REX Button", 'rex_button'),
            ("Push Button w/ Indicator", 'push_button'),
            ("Break Glass", 'break_glass'),
            ("Buzzer", 'buzzer'),
            ("Double Door Lock", 'double_door_lock'),
            ("DDL Sensors", 'ddl_sensors')
        ]
        
        for display_name, attr_name in devices:
            while True:
                try:
                    value = int(input(f"{display_name}: "))
                    if value < 0:
                        print("Enter 0 or positive number")
                        continue
                    setattr(dc_line, attr_name, value)
                    break
                except ValueError:
                    print("Enter a valid number")
        
        self.dc_lines.append(dc_line)
        totals = dc_line.calculate_totals()
        
        print(f"\n✅ DC Line {dc_number} added:")
        print(f"   Readers: {totals['readers']}")
        print(f"   Inputs:  {totals['inputs']}")
        print(f"   Outputs: {totals['outputs']}")
        
        input("\nPress Enter to continue...")
    
    def edit_dc_line_interactive(self):
        """Edit an existing DC line"""
        if not self.dc_lines:
            print("No DC lines configured yet!")
            input("Press Enter to continue...")
            return
        
        self.clear_screen()
        self.print_header("EDIT DC LINE CONFIGURATION")
        
        print("Select DC line to edit:")
        for dc_line in self.dc_lines:
            totals = dc_line.calculate_totals()
            print(f"DC Line {dc_line.dc_number}: {totals['readers']} readers, "
                  f"{totals['inputs']} inputs, {totals['outputs']} outputs")
        
        try:
            dc_num = int(input("\nEnter DC line number to edit: "))
            
            # Find the DC line
            dc_line = next((dc for dc in self.dc_lines if dc.dc_number == dc_num), None)
            
            if not dc_line:
                print(f"DC Line {dc_num} not found!")
                input("Press Enter to continue...")
                return
            
            self.clear_screen()
            self.print_header(f"EDIT DC LINE {dc_num}")
            
            print("Current values in [brackets]. Press Enter to keep current value.")
            print()
            
            devices = [
                ("INDOOR Smart Card Reader", 'smart_card'),
                ("Finger Print Reader", 'fingerprint'),
                ("Door Sensor", 'door_sensor'),
                ("Magnetic Door Lock", 'magnetic_lock'),
                ("Electric Door Lock", 'electric_lock'),
                ("REX Button", 'rex_button'),
                ("Push Button w/ Indicator", 'push_button'),
                ("Break Glass", 'break_glass'),
                ("Buzzer", 'buzzer'),
                ("Double Door Lock", 'double_door_lock'),
                ("DDL Sensors", 'ddl_sensors')
            ]
            
            for display_name, attr_name in devices:
                current_value = getattr(dc_line, attr_name)
                while True:
                    try:
                        value_str = input(f"{display_name} [{current_value}]: ").strip()
                        if value_str == "":
                            value = current_value  # Keep current value
                        else:
                            value = int(value_str)
                            if value < 0:
                                print("Enter 0 or positive number")
                                continue
                        
                        setattr(dc_line, attr_name, value)
                        break
                    except ValueError:
                        print("Enter a valid number or press Enter to keep current value")
            
            totals = dc_line.calculate_totals()
            
            print(f"\n✅ DC Line {dc_num} updated:")
            print(f"   Readers: {totals['readers']}")
            print(f"   Inputs:  {totals['inputs']}")
            print(f"   Outputs: {totals['outputs']}")
            
        except ValueError:
            print("Please enter a valid DC line number!")
        
        input("\nPress Enter to continue...")
    
    def select_controllers_for_dc(self, dc_requirements: Dict) -> Dict:
        """Select controllers for a SINGLE DC line based ONLY on reader count"""
        total_readers = dc_requirements['readers']
        
        # Find optimal controller combination for readers only
        best_solution = None
        best_cost = float('inf')
        
        # Maximum possible of each controller type
        max_kt400 = max(1, total_readers // 4 + 2)
        max_kt2 = max(1, total_readers // 2 + 2)
        max_kt1 = max(1, total_readers + 2)
        
        for kt400 in range(max_kt400 + 1):
            for kt2 in range(max_kt2 + 1):
                for kt1 in range(max_kt1 + 1):
                    readers_provided = (kt400 * 4 + kt2 * 2 + kt1 * 1)
                    cost = (kt400 * 1400 + kt2 * 750 + kt1 * 450)
                    
                    # Must meet or exceed reader requirements
                    if readers_provided >= total_readers:
                        if cost < best_cost:
                            best_cost = cost
                            best_solution = {
                                'kt-400': kt400,
                                'kt-2': kt2,
                                'kt-1': kt1,
                                'readers_provided': readers_provided,
                                'cost': cost,
                                'extra_readers': readers_provided - total_readers
                            }
        
        if best_solution:
            # Calculate inputs/outputs provided by these controllers
            inputs_provided = (best_solution['kt-400'] * 16 + 
                             best_solution['kt-2'] * 8 + 
                             best_solution['kt-1'] * 4)
            
            outputs_provided = (best_solution['kt-400'] * 4 + 
                              best_solution['kt-2'] * 2 + 
                              best_solution['kt-1'] * 2)
            
            return {
                **best_solution,
                'inputs_provided': inputs_provided,
                'outputs_provided': outputs_provided
            }
        
        return None
    
    def calculate_expansion_for_dc(self, dc_inputs: int, dc_outputs: int, 
                                 controller_inputs: int, controller_outputs: int) -> Dict:
        """Calculate expansion modules needed for a SINGLE DC line"""
        # Calculate shortages
        input_shortage = max(0, dc_inputs - controller_inputs)
        output_shortage = max(0, dc_outputs - controller_outputs)
        
        print(f"\nI/O Analysis:")
        print(f"  Required: {dc_inputs} inputs, {dc_outputs} outputs")
        print(f"  Controllers provide: {controller_inputs} inputs, {controller_outputs} outputs")
        print(f"  Shortage: {input_shortage} inputs, {output_shortage} outputs")
        
        if input_shortage == 0 and output_shortage == 0:
            print("  ✅ No expansion modules needed")
            return {'modules': [], 'cost': 0}
        
        # Try different module combinations to find the cheapest
        best_solution = {'modules': [], 'cost': float('inf')}
        
        # Try single module that covers both needs
        for module in self.expansion_modules:
            if module['inputs'] >= input_shortage and module['outputs'] >= output_shortage:
                solution = {
                    'modules': [module['name']],
                    'cost': module['cost']
                }
                if solution['cost'] < best_solution['cost']:
                    best_solution = solution
        
        # Try combinations of two modules
        for module1 in self.expansion_modules:
            for module2 in self.expansion_modules:
                total_inputs = module1['inputs'] + module2['inputs']
                total_outputs = module1['outputs'] + module2['outputs']
                total_cost = module1['cost'] + module2['cost']
                
                if total_inputs >= input_shortage and total_outputs >= output_shortage:
                    solution = {
                        'modules': [module1['name'], module2['name']],
                        'cost': total_cost
                    }
                    if solution['cost'] < best_solution['cost']:
                        best_solution = solution
        
        # If no solution found with up to 2 modules, use specialized modules
        if best_solution['cost'] == float('inf'):
            expansion_modules = []
            expansion_cost = 0
            
            # Add input modules if needed
            if input_shortage > 0:
                # Use in16 modules (16 inputs each)
                in16_needed = int(np.ceil(input_shortage / 16))
                expansion_modules.append(f"in16 (x{in16_needed})")
                expansion_cost += 470 * in16_needed
            
            # Add output modules if needed
            if output_shortage > 0:
                # Use r8 modules (8 outputs each)
                r8_needed = int(np.ceil(output_shortage / 8))
                expansion_modules.append(f"r8 (x{r8_needed})")
                expansion_cost += 470 * r8_needed
            
            best_solution = {
                'modules': expansion_modules,
                'cost': expansion_cost
            }
        
        print(f"  Expansion solution: {best_solution['modules']}")
        print(f"  Expansion cost: ${best_solution['cost']}")
        
        return best_solution
    
    def calculate_total_controllers(self):
        """Calculate total number of controllers needed for ALL DC lines"""
        if not self.dc_lines:
            return {'total_controllers': 0, 'kt-400': 0, 'kt-2': 0, 'kt-1': 0}
        
        total_kt400 = 0
        total_kt2 = 0
        total_kt1 = 0
        
        for dc_line in self.dc_lines:
            dc_totals = dc_line.calculate_totals()
            controller_info = self.select_controllers_for_dc(dc_totals)
            
            if controller_info:
                total_kt400 += controller_info['kt-400']
                total_kt2 += controller_info['kt-2']
                total_kt1 += controller_info['kt-1']
        
        total_controllers = total_kt400 + total_kt2 + total_kt1
        
        return {
            'total_controllers': total_controllers,
            'kt-400': total_kt400,
            'kt-2': total_kt2,
            'kt-1': total_kt1,
            'breakdown': f"kt-400: {total_kt400}, kt-2: {total_kt2}, kt-1: {total_kt1}"
        }
    
    def calculate_license_requirements(self, use_redundancy=False):
        """Calculate license requirements based on total controllers"""
        self.clear_screen()
        self.print_header("LICENSE CALCULATION")
        
        # Calculate total controllers
        controller_totals = self.calculate_total_controllers()
        total_controllers = controller_totals['total_controllers']
        
        print("📊 CONTROLLER SUMMARY:")
        print("-" * 40)
        print(f"Total Controllers Needed: {total_controllers}")
        print(f"Controller Breakdown:")
        print(f"  kt-400: {controller_totals['kt-400']} units")
        print(f"  kt-2:   {controller_totals['kt-2']} units")
        print(f"  kt-1:   {controller_totals['kt-1']} units")
        print()
        
        print("🎫 LICENSE REQUIREMENTS:")
        print("-" * 40)
        
        # Determine license type based on controller count
        if total_controllers == 0:
            print("❌ No controllers configured!")
            print("Please add DC lines and calculate controllers first.")
            input("\nPress Enter to continue...")
            return
        
        # UPDATED LOGIC: When redundancy is needed, ALWAYS use Global License
        if use_redundancy:
            print(f"🔴 REDUNDANCY CONFIGURATION SELECTED")
            print(f"✅ Required License: {self.license_info['global']['name']}")
            print(f"   Reason: Redundancy requires Global License (replaces Special/Corporate)")
            print(f"   Description: {self.license_info['global']['description']}")
            
            # Additional licenses for redundancy configuration
            print(f"\n➕ ADDITIONAL LICENSES FOR REDUNDANCY:")
            print(f"   1. {self.license_info['gateway']['name']}")
            print(f"      Cost: ${self.license_info['gateway']['cost']}")
            print(f"      Description: {self.license_info['gateway']['description']}")
            
            print(f"\n   2. {self.license_info['redundancy']['name']}")
            print(f"      Cost: ${self.license_info['redundancy']['cost']}")
            print(f"      Description: {self.license_info['redundancy']['description']}")
            
            license_type = 'global'
            additional_licenses = [
                {'name': self.license_info['gateway']['name'], 'cost': self.license_info['gateway']['cost']},
                {'name': self.license_info['redundancy']['name'], 'cost': self.license_info['redundancy']['cost']}
            ]
            
        else:
            # Non-redundant configuration
            if total_controllers <= 32:
                license_type = 'special'
                print(f"✅ Required License: {self.license_info['special']['name']}")
                print(f"   Reason: {total_controllers} controllers ≤ 32")
                print(f"   Description: {self.license_info['special']['description']}")
            else:
                license_type = 'corporate'
                print(f"✅ Required License: {self.license_info['corporate']['name']}")
                print(f"   Reason: {total_controllers} controllers > 32")
                print(f"   Description: {self.license_info['corporate']['description']}")
            
            additional_licenses = []
        
        # Calculate total license cost
        total_license_cost = 0
        if use_redundancy:
            total_license_cost = (self.license_info['gateway']['cost'] + 
                                 self.license_info['redundancy']['cost'])
        
        # Summary
        print("\n" + "=" * 60)
        print("📝 LICENSE SUMMARY:")
        print("-" * 60)
        print(f"Total Controllers: {total_controllers}")
        print(f"Configuration: {'Redundant' if use_redundancy else 'Non-Redundant'}")
        print()
        
        if use_redundancy:
            print(f"PRIMARY LICENSE:")
            print(f"  • {self.license_info['global']['name']}")
            print(f"\nADDITIONAL LICENSES:")
            for license_item in additional_licenses:
                print(f"  • {license_item['name']}: ${license_item['cost']}")
            print(f"\nTOTAL LICENSE COST: ${total_license_cost}")
        else:
            if total_controllers <= 32:
                print(f"PRIMARY LICENSE:")
                print(f"  • {self.license_info['special']['name']}")
            else:
                print(f"PRIMARY LICENSE:")
                print(f"  • {self.license_info['corporate']['name']}")
            print(f"\nADDITIONAL LICENSES: None")
            print(f"TOTAL LICENSE COST: $0 (included in controller cost)")
        
        print("\n" + "=" * 60)
        
        # Store license info for export
        self.license_result = {
            'total_controllers': total_controllers,
            'primary_license': license_type,
            'use_redundancy': use_redundancy,
            'additional_licenses': additional_licenses,
            'total_license_cost': total_license_cost,
            'controller_breakdown': controller_totals
        }
        
        input("\nPress Enter to continue...")
    
    def calculate_single_dc_line(self, dc_line: DCDevice):
        """Calculate system for a SINGLE DC line"""
        self.clear_screen()
        self.print_header(f"DC LINE {dc_line.dc_number} CALCULATION")
        
        # Get DC line requirements
        dc_totals = dc_line.calculate_totals()
        
        print("📊 DC LINE REQUIREMENTS:")
        print("-" * 40)
        print(f"Readers: {dc_totals['readers']}")
        print(f"Inputs:  {dc_totals['inputs']}")
        print(f"Outputs: {dc_totals['outputs']}")
        print()
        
        # Step 1: Select controllers based ONLY on readers
        print("STEP 1: SELECT CONTROLLERS (Based on readers only)")
        print("-" * 40)
        
        controller_info = self.select_controllers_for_dc(dc_totals)
        
        if not controller_info:
            print("❌ No controller combination found for this DC line!")
            input("Press Enter to continue...")
            return None
        
        print(f"\n✅ Selected Controllers for DC Line {dc_line.dc_number}:")
        print(f"   kt-400: {controller_info['kt-400']} units")
        print(f"   kt-2:   {controller_info['kt-2']} units")
        print(f"   kt-1:   {controller_info['kt-1']} units")
        print(f"   Controller Cost: ${controller_info['cost']}")
        
        print(f"\n📈 Controller Capabilities:")
        print(f"   Readers provided: {controller_info['readers_provided']} ({controller_info['extra_readers']} extra)")
        print(f"   Inputs provided:  {controller_info['inputs_provided']}")
        print(f"   Outputs provided: {controller_info['outputs_provided']}")
        
        # Step 2: Calculate expansion modules for inputs/outputs
        print("\n" + "=" * 60)
        print("STEP 2: CALCULATE EXPANSION MODULES")
        print("-" * 40)
        
        expansion = self.calculate_expansion_for_dc(
            dc_totals['inputs'],
            dc_totals['outputs'],
            controller_info['inputs_provided'],
            controller_info['outputs_provided']
        )
        
        # Display final results
        print("\n" + "=" * 60)
        print("💰 FINAL COST BREAKDOWN:")
        print("-" * 40)
        total_cost = controller_info['cost'] + expansion['cost']
        print(f"   Controllers: ${controller_info['cost']}")
        print(f"   Expansion:   ${expansion['cost']}")
        print(f"   {'TOTAL:':<12} ${total_cost}")
        print("=" * 60)
        
        # Return calculation results
        return {
            'dc_number': dc_line.dc_number,
            'requirements': dc_totals,
            'controllers': controller_info,
            'expansion': expansion,
            'total_cost': total_cost
        }
    
    def calculate_all_dc_lines(self):
        """Calculate system for EACH DC line individually"""
        if not self.dc_lines:
            print("No DC lines configured!")
            input("Press Enter to continue...")
            return
        
        all_results = []
        
        for dc_line in self.dc_lines:
            result = self.calculate_single_dc_line(dc_line)
            if result:
                all_results.append(result)
                if dc_line != self.dc_lines[-1]:  # If not the last DC line
                    input("\nPress Enter to see next DC line...")
        
        if not all_results:
            return
        
        # Display summary of all DC lines
        self.clear_screen()
        self.print_header("ALL DC LINES CALCULATION SUMMARY")
        
        print("📋 SUMMARY OF ALL DC LINES:")
        print("=" * 90)
        print(f"{'DC Line':<8} {'Requirements':<20} {'Controllers':<25} {'Expansion':<25} {'Total Cost':<12}")
        print("-" * 90)
        
        grand_total_cost = 0
        total_kt400 = 0
        total_kt2 = 0
        total_kt1 = 0
        total_expansion_cost = 0
        
        for result in all_results:
            req = result['requirements']
            controllers = result['controllers']
            expansion = result['expansion']
            total_cost = result['total_cost']
            
            # Build requirement string
            req_str = f"{req['readers']}R/{req['inputs']}I/{req['outputs']}O"
            
            # Build controller string
            controller_str = ""
            if controllers['kt-400'] > 0:
                controller_str += f"kt-400({controllers['kt-400']}) "
            if controllers['kt-2'] > 0:
                controller_str += f"kt-2({controllers['kt-2']}) "
            if controllers['kt-1'] > 0:
                controller_str += f"kt-1({controllers['kt-1']}) "
            if not controller_str:
                controller_str = "None"
            
            # Build expansion string
            expansion_str = ", ".join(expansion['modules']) if expansion['modules'] else "None"
            
            print(f"{result['dc_number']:<8} {req_str:<20} {controller_str:<25} {expansion_str:<25} ${total_cost:<10}")
            
            # Accumulate totals
            grand_total_cost += total_cost
            total_kt400 += controllers['kt-400']
            total_kt2 += controllers['kt-2']
            total_kt1 += controllers['kt-1']
            total_expansion_cost += expansion['cost']
        
        print("-" * 90)
        print(f"{'GRAND TOTAL':<78} ${grand_total_cost}")
        print()
        
        print("\n📊 TOTAL CONTROLLERS NEEDED:")
        print("-" * 40)
        print(f"kt-400: {total_kt400} units  (${total_kt400 * 1400})")
        print(f"kt-2:   {total_kt2} units  (${total_kt2 * 750})")
        print(f"kt-1:   {total_kt1} units  (${total_kt1 * 450})")
        print(f"Total controller cost: ${total_kt400 * 1400 + total_kt2 * 750 + total_kt1 * 450}")
        print(f"Total expansion cost:  ${total_expansion_cost}")
        print(f"GRAND TOTAL:           ${grand_total_cost}")
        
        # Calculate total controllers for license reference
        total_controllers = total_kt400 + total_kt2 + total_kt1
        print(f"\n🎫 LICENSE REFERENCE:")
        print("-" * 40)
        if total_controllers <= 32:
            print(f"Total Controllers: {total_controllers} → Kantech Special License")
            print(f"Note: For redundancy, migrate to Global License + Gateway + Redundancy licenses")
        else:
            print(f"Total Controllers: {total_controllers} → Kantech Corporate License")
            print(f"Note: For redundancy, migrate to Global License + Gateway + Redundancy licenses")
        
        # Store all results for export
        self.all_results = all_results
        self.grand_total = grand_total_cost
        
        input("\nPress Enter to continue...")
    
    def view_dc_summary(self):
        """View all DC lines and their requirements"""
        self.clear_screen()
        self.print_header("DC LINE CONFIGURATION SUMMARY")
        
        if not self.dc_lines:
            print("No DC lines configured yet!")
            input("Press Enter to continue...")
            return
        
        print(f"{'DC Line':<8} {'Smart Card':<12} {'Fingerprint':<12} {'Double Door':<12} {'Readers':<10} {'Inputs':<10} {'Outputs':<10}")
        print("-" * 90)
        
        for dc_line in self.dc_lines:
            totals = dc_line.calculate_totals()
            
            print(f"{dc_line.dc_number:<8} {dc_line.smart_card:<12} {dc_line.fingerprint:<12} "
                  f"{dc_line.double_door_lock:<12} {totals['readers']:<10} {totals['inputs']:<10} {totals['outputs']:<10}")
        
        print("\n" + "=" * 90)
        print("NOTE: Each DC line is calculated INDIVIDUALLY")
        
        input("\nPress Enter to continue...")
    
    def calculate_specific_dc_line(self):
        """Calculate system for a SPECIFIC DC line"""
        if not self.dc_lines:
            print("No DC lines configured!")
            input("Press Enter to continue...")
            return
        
        self.clear_screen()
        self.print_header("CALCULATE SPECIFIC DC LINE")
        
        print("Available DC Lines:")
        for dc_line in self.dc_lines:
            totals = dc_line.calculate_totals()
            print(f"DC Line {dc_line.dc_number}: {totals['readers']} readers, "
                  f"{totals['inputs']} inputs, {totals['outputs']} outputs")
        
        try:
            dc_num = int(input("\nEnter DC line number to calculate: "))
            
            # Find the DC line
            dc_line = next((dc for dc in self.dc_lines if dc.dc_number == dc_num), None)
            
            if dc_line:
                result = self.calculate_single_dc_line(dc_line)
                if result:
                    # Store for export
                    if not hasattr(self, 'single_result'):
                        self.single_result = []
                    self.single_result.append(result)
                    
                    # Ask user what to do next
                    print("\nOptions:")
                    print("1. Return to main menu")
                    print("2. Calculate another DC line")
                    
                    choice = input("\nSelect option (1-2): ")
                    if choice == '2':
                        self.calculate_specific_dc_line()
            else:
                print(f"DC Line {dc_num} not found!")
                input("Press Enter to continue...")
                
        except ValueError:
            print("Please enter a valid DC line number!")
            input("Press Enter to continue...")
    
    def export_all_results_to_csv(self):
        """Export ALL DC line results to CSV"""
        if not hasattr(self, 'all_results'):
            print("Please run calculations for all DC lines first!")
            input("Press Enter to continue...")
            return
        
        self.clear_screen()
        self.print_header("EXPORT ALL DC LINE RESULTS")
        
        filename = input("Enter filename (default: kantech_dc_lines.csv): ").strip()
        if not filename:
            filename = "kantech_dc_lines.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # Create DataFrame for export
        data = []
        
        # Add each DC line's results
        for result in self.all_results:
            dc_num = result['dc_number']
            req = result['requirements']
            controllers = result['controllers']
            expansion = result['expansion']
            
            # DC line requirements
            data.append({
                'DC_Line': dc_num,
                'Type': 'Requirements',
                'Readers': req['readers'],
                'Inputs': req['inputs'],
                'Outputs': req['outputs'],
                'KT400': '',
                'KT2': '',
                'KT1': '',
                'Controller_Cost': '',
                'Expansion_Modules': '',
                'Expansion_Cost': '',
                'Total_Cost': ''
            })
            
            # Controllers for this DC line
            data.append({
                'DC_Line': dc_num,
                'Type': 'Controllers',
                'Readers': controllers['readers_provided'],
                'Inputs': controllers['inputs_provided'],
                'Outputs': controllers['outputs_provided'],
                'KT400': controllers['kt-400'],
                'KT2': controllers['kt-2'],
                'KT1': controllers['kt-1'],
                'Controller_Cost': controllers['cost'],
                'Expansion_Modules': '',
                'Expansion_Cost': '',
                'Total_Cost': ''
            })
            
            # Expansion modules for this DC line
            if expansion['modules']:
                modules_str = ', '.join(expansion['modules'])
                data.append({
                    'DC_Line': dc_num,
                    'Type': 'Expansion',
                    'Readers': '',
                    'Inputs': '',
                    'Outputs': '',
                    'KT400': '',
                    'KT2': '',
                    'KT1': '',
                    'Controller_Cost': '',
                    'Expansion_Modules': modules_str,
                    'Expansion_Cost': expansion['cost'],
                    'Total_Cost': ''
                })
            else:
                data.append({
                    'DC_Line': dc_num,
                    'Type': 'Expansion',
                    'Readers': '',
                    'Inputs': '',
                    'Outputs': '',
                    'KT400': '',
                    'KT2': '',
                    'KT1': '',
                    'Controller_Cost': '',
                    'Expansion_Modules': 'None',
                    'Expansion_Cost': 0,
                    'Total_Cost': ''
                })
            
            # Total for this DC line
            data.append({
                'DC_Line': dc_num,
                'Type': 'TOTAL',
                'Readers': '',
                'Inputs': '',
                'Outputs': '',
                'KT400': '',
                'KT2': '',
                'KT1': '',
                'Controller_Cost': '',
                'Expansion_Modules': '',
                'Expansion_Cost': '',
                'Total_Cost': result['total_cost']
            })
            
            # Add empty row between DC lines
            data.append({
                'DC_Line': '',
                'Type': '',
                'Readers': '',
                'Inputs': '',
                'Outputs': '',
                'KT400': '',
                'KT2': '',
                'KT1': '',
                'Controller_Cost': '',
                'Expansion_Modules': '',
                'Expansion_Cost': '',
                'Total_Cost': ''
            })
        
        # Add license information if available
        if hasattr(self, 'license_result'):
            license_info = self.license_result
            
            # Primary license info
            if license_info['use_redundancy']:
                primary_license_name = self.license_info['global']['name']
            elif license_info['total_controllers'] <= 32:
                primary_license_name = self.license_info['special']['name']
            else:
                primary_license_name = self.license_info['corporate']['name']
            
            data.append({
                'DC_Line': 'LICENSE INFO',
                'Type': 'System Configuration',
                'Readers': f"{'Redundant' if license_info['use_redundancy'] else 'Non-Redundant'}",
                'Inputs': f"Total Controllers: {license_info['total_controllers']}",
                'Outputs': '',
                'KT400': '',
                'KT2': '',
                'KT1': '',
                'Controller_Cost': '',
                'Expansion_Modules': '',
                'Expansion_Cost': '',
                'Total_Cost': ''
            })
            
            data.append({
                'DC_Line': 'LICENSE INFO',
                'Type': 'Primary License',
                'Readers': primary_license_name,
                'Inputs': '',
                'Outputs': '',
                'KT400': '',
                'KT2': '',
                'KT1': '',
                'Controller_Cost': '',
                'Expansion_Modules': '',
                'Expansion_Cost': '',
                'Total_Cost': ''
            })
            
            # Additional licenses if redundancy
            if license_info['use_redundancy']:
                for license_item in license_info['additional_licenses']:
                    data.append({
                        'DC_Line': 'LICENSE INFO',
                        'Type': 'Additional License',
                        'Readers': license_item['name'],
                        'Inputs': f"Cost: ${license_item['cost']}",
                        'Outputs': '',
                        'KT400': '',
                        'KT2': '',
                        'KT1': '',
                        'Controller_Cost': '',
                        'Expansion_Modules': '',
                        'Expansion_Cost': '',
                        'Total_Cost': ''
                    })
                
                data.append({
                    'DC_Line': 'LICENSE INFO',
                    'Type': 'Total License Cost',
                    'Readers': f"${license_info['total_license_cost']}",
                    'Inputs': '',
                    'Outputs': '',
                    'KT400': '',
                    'KT2': '',
                    'KT1': '',
                    'Controller_Cost': '',
                    'Expansion_Modules': '',
                    'Expansion_Cost': '',
                    'Total_Cost': ''
                })
        
        # Add grand total
        total_kt400 = sum(r['controllers']['kt-400'] for r in self.all_results)
        total_kt2 = sum(r['controllers']['kt-2'] for r in self.all_results)
        total_kt1 = sum(r['controllers']['kt-1'] for r in self.all_results)
        total_controller_cost = sum(r['controllers']['cost'] for r in self.all_results)
        total_expansion_cost = sum(r['expansion']['cost'] for r in self.all_results)
        
        data.append({
            'DC_Line': 'GRAND TOTAL',
            'Type': 'Summary',
            'Readers': '',
            'Inputs': '',
            'Outputs': '',
            'KT400': total_kt400,
            'KT2': total_kt2,
            'KT1': total_kt1,
            'Controller_Cost': total_controller_cost,
            'Expansion_Modules': '',
            'Expansion_Cost': total_expansion_cost,
            'Total_Cost': self.grand_total
        })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        
        print(f"\n✅ All DC line results exported to {filename}")
        input("\nPress Enter to continue...")
    
    def main_menu(self):
        """Display main menu"""
        while True:
            self.clear_screen()
            self.print_header("KANTECH DC LINE CALCULATOR")
            
            print("PER DC LINE CALCULATION LOGIC:")
            print("1. Each DC line calculated INDIVIDUALLY")
            print("2. Controllers selected based on DC line's reader count ONLY")
            print("3. Expansion modules added for DC line's I/O requirements")
            print("4. License Rules:")
            print("   - ≤ 32 controllers: Special License")
            print("   - > 32 controllers: Corporate License")
            print("   - Redundancy: Global License + Gateway + Redundancy licenses")
            print()
            
            if self.dc_lines:
                print(f"Current: {len(self.dc_lines)} DC line(s) configured")
                print("DC Lines:", ", ".join([f"DC{dc.dc_number}" for dc in self.dc_lines]))
                
                # Show total requirements
                total_readers = sum(dc.calculate_totals()['readers'] for dc in self.dc_lines)
                total_inputs = sum(dc.calculate_totals()['inputs'] for dc in self.dc_lines)
                total_outputs = sum(dc.calculate_totals()['outputs'] for dc in self.dc_lines)
                print(f"Total Requirements: {total_readers} readers, {total_inputs} inputs, {total_outputs} outputs")
                
                # Show total controllers if calculated
                if hasattr(self, 'all_results'):
                    total_controllers = sum(r['controllers']['kt-400'] + r['controllers']['kt-2'] + r['controllers']['kt-1'] 
                                          for r in self.all_results)
                    print(f"Total Controllers: {total_controllers}")
                    
                    # Show license recommendation
                    if hasattr(self, 'license_result') and self.license_result['use_redundancy']:
                        print(f"License: Global License + Gateway + Redundancy (Redundant System)")
                    elif total_controllers <= 32:
                        print(f"License: Kantech Special License")
                    else:
                        print(f"License: Kantech Corporate License")
            else:
                print("No DC lines configured yet")
            print()
            
            print("MAIN MENU:")
            print("1. Add DC Line Configuration")
            print("2. Edit DC Line Configuration")
            print("3. View DC Lines Summary")
            print("4. Calculate Specific DC Line")
            print("5. Calculate ALL DC Lines")
            print("6. Calculate License Requirements")
            print("7. Export ALL DC Line Results")
            print("8. Clear All Data")
            print("9. Exit")
            print()
            
            try:
                choice = int(input("Select option (1-9): "))
            except ValueError:
                print("Enter a number 1-9")
                input("Press Enter to continue...")
                continue
            
            if choice == 1:
                self.add_dc_line_interactive()
            elif choice == 2:
                self.edit_dc_line_interactive()
            elif choice == 3:
                self.view_dc_summary()
            elif choice == 4:
                self.calculate_specific_dc_line()
            elif choice == 5:
                self.calculate_all_dc_lines()
            elif choice == 6:
                self.calculate_license_menu()
            elif choice == 7:
                self.export_all_results_to_csv()
            elif choice == 8:
                self.dc_lines.clear()
                print("All DC line data cleared!")
                input("Press Enter to continue...")
            elif choice == 9:
                print("\nThank you for using Kantech DC Line Calculator!")
                break
            else:
                print("Invalid choice!")
                input("Press Enter to continue...")
    
    def calculate_license_menu(self):
        """Menu for calculating license requirements"""
        self.clear_screen()
        self.print_header("CALCULATE LICENSE REQUIREMENTS")
        
        print("LICENSE RULES:")
        print("-" * 40)
        print("1. NON-REDUNDANT SYSTEMS:")
        print("   • ≤ 32 controllers → Kantech Special License")
        print("   • > 32 controllers → Kantech Corporate License")
        print()
        print("2. REDUNDANT SYSTEMS:")
        print("   • Migrate to Global License (replaces Special/Corporate)")
        print("   • Add Gateway License (for server communication)")
        print("   • Add Redundancy License (for failover capability)")
        print()
        
        # Ask about redundancy
        print("Do you need redundancy configuration?")
        
        print("(Redundancy provides backup/failover capability)")
        print()
        print("1. Yes, I need redundancy (Global + Gateway + Redundancy licenses)")
        print("2. No, redundancy not needed (Special or Corporate license only)")
        print()
        
        try:
            redundancy_choice = int(input("Select option (1-2): "))
            use_redundancy = (redundancy_choice == 1)
            
            # Calculate license requirements
            self.calculate_license_requirements(use_redundancy)
            
        except ValueError:
            print("Invalid input! Please enter 1 or 2.")
            input("Press Enter to continue...")

def main():
    """Run the calculator"""
    print("Loading Kantech DC Line Calculator...")
    print("Each DC line calculated INDIVIDUALLY")
    print("License Rules:")
    print("- ≤ 32 controllers: Special License")
    print("- > 32 controllers: Corporate License")
    print("- Redundancy: Global License + Gateway + Redundancy licenses")
    input("Press Enter to start...")
    
    calculator = KantechDCCalculator()
    calculator.main_menu()

if __name__ == "__main__":
    main()