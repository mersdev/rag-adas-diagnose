# Mercedes-Benz E-Class Engine Control System Diagnostics
## E350 2.0L Turbocharged Engine (M264) | VIN Pattern: WDD213*

### Engine Overview
The Mercedes-Benz E350 2.0L turbocharged direct injection engine (M264) features advanced emission controls, EQBoost mild hybrid technology, and integrated ADAS functionality. The engine management system coordinates with 9G-TRONIC transmission, brake, and steering systems for optimal performance and efficiency.

### Mercedes-Benz E-Class Engine Control Module (ECM)
- **Part Number**: A274-150-79-79 (M264 Engine Control Unit)
- **Supplier**: Bosch ME17.7.8
- **Software Calibration**: MB-SW-274-V3.2.1
- **Hardware Version**: HW-4.1
- **CAN Bus Address**: 0x7E8
- **Mercedes Star Diagnosis Code**: N3/10

### Sensor Network

#### Mass Airflow Sensor (MAF)
- **Location**: Intake tube, post-air filter
- **Operating Range**: 0-650 kg/h
- **Signal Type**: Analog voltage 0.5-4.5V
- **Part Number**: MAF-T20-001

#### Manifold Absolute Pressure (MAP)
- **Operating Range**: 10-250 kPa
- **Accuracy**: ±2 kPa
- **Response Time**: < 10ms
- **Part Number**: MAP-T20-002

#### Oxygen Sensors (O2)
- **Type**: Wideband UEGO
- **Quantity**: 2 (upstream/downstream)
- **Operating Temperature**: 300-900°C
- **Lambda Range**: 0.65-1.35

### Common Diagnostic Trouble Codes

#### P0300 - Random/Multiple Cylinder Misfire
**Symptoms**:
- Engine roughness at idle
- Reduced power output
- Increased emissions
- Check engine light

**Diagnostic Procedure**:
1. Check spark plugs and coils
2. Verify fuel pressure (55-62 psi)
3. Test compression (minimum 150 psi)
4. Inspect intake manifold for leaks
5. Check fuel injector operation

**Common Causes**:
- Worn spark plugs (replace every 60,000 miles)
- Faulty ignition coils
- Clogged fuel injectors
- Carbon buildup on intake valves

#### P0171 - System Too Lean (Bank 1)
**Symptoms**:
- Poor fuel economy
- Hesitation during acceleration
- Rough idle
- Possible stalling

**Diagnostic Procedure**:
1. Check for vacuum leaks using smoke test
2. Verify MAF sensor operation (2.5-3.5V at idle)
3. Test fuel pressure and volume
4. Inspect PCV system operation
5. Check exhaust system for leaks

#### P0234 - Turbocharger Overboost Condition
**Symptoms**:
- Reduced engine power
- Turbo whistle or unusual noise
- Black smoke from exhaust
- Limp mode activation

**Diagnostic Procedure**:
1. Check wastegate actuator operation
2. Verify boost pressure sensor readings
3. Inspect intercooler for leaks
4. Test wastegate solenoid valve
5. Check for intake restrictions

### Turbocharger System

#### Turbocharger Specifications
- **Type**: Variable geometry (VGT)
- **Maximum Boost**: 1.8 bar (26 psi)
- **Compressor Wheel**: Aluminum alloy
- **Turbine Wheel**: Inconel
- **Oil Supply Pressure**: 1.5-4.0 bar

#### Wastegate Control
- **Actuator Type**: Electronic
- **Control Range**: 0-100% duty cycle
- **Response Time**: < 200ms
- **Calibration**: Requires scan tool

### Fuel System

#### High Pressure Fuel Pump
- **Type**: Mechanical, cam-driven
- **Operating Pressure**: 200 bar (2900 psi)
- **Flow Rate**: 180 L/h at maximum
- **Drive**: Intake camshaft lobe

#### Fuel Injectors
- **Type**: Piezo electric, direct injection
- **Flow Rate**: 1200 cc/min at 300 bar
- **Spray Pattern**: 6-hole, 60° cone
- **Part Number**: INJ-DI-T20-001

### Emission Control Systems

#### Catalytic Converter
- **Type**: Three-way catalyst with GPF
- **Substrate**: Ceramic honeycomb
- **Precious Metals**: Pt, Pd, Rh
- **Light-off Temperature**: 250°C

#### EGR System
- **Type**: Cooled, electronically controlled
- **Flow Rate**: 0-25% of total airflow
- **Cooler Type**: Liquid-cooled
- **Valve Type**: Electric motor driven

### Performance Parameters

#### Normal Operating Values
- **Idle Speed**: 750 ± 50 RPM
- **Coolant Temperature**: 88-105°C
- **Oil Pressure**: 1.5 bar at idle, 4.0 bar at 3000 RPM
- **Fuel Pressure**: 55-62 psi (low pressure), 200 bar (high pressure)
- **Intake Air Temperature**: Ambient + 10-15°C

### Maintenance Intervals

#### Engine Oil
- **Type**: 0W-20 full synthetic
- **Capacity**: 4.5L with filter
- **Interval**: 10,000 miles or 12 months
- **Filter**: High-efficiency synthetic media

#### Air Filter
- **Type**: Paper element with pre-filter
- **Interval**: 30,000 miles (severe duty: 15,000)
- **Part Number**: AF-T20-001

#### Spark Plugs
- **Type**: Iridium electrode
- **Gap**: 0.7mm (0.028")
- **Torque**: 25 Nm (18 ft-lbs)
- **Interval**: 60,000 miles

### ADAS Integration

#### Engine Torque Management
- Coordinates with ACC for smooth speed control
- Provides torque reduction for stability systems
- Integrates with start-stop functionality

#### Predictive Efficiency
- Uses navigation data for optimal shift points
- Adjusts engine mapping for traffic conditions
- Coordinates with hybrid system (if equipped)

### Troubleshooting Quick Reference

| Symptom | Likely Cause | First Check |
|---------|--------------|-------------|
| No Start | Fuel/Ignition | Fuel pressure, spark |
| Rough Idle | Vacuum leak | Smoke test intake |
| Poor Power | Turbo issue | Boost pressure |
| High Emissions | Catalyst | O2 sensor readings |
| Overheating | Cooling system | Coolant level/flow |

### Safety Precautions
⚠️ **HIGH PRESSURE**: Fuel system operates at 200 bar - relieve pressure before service
⚠️ **HOT SURFACES**: Turbocharger and exhaust reach 700°C+ during operation
⚠️ **ELECTRICAL**: Disconnect battery before ECM service
