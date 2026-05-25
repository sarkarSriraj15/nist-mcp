import pytest

@pytest.fixture
def mock_shomate_html():
    return """
    <h3>Gas Phase Heat Capacity (Shomate Equation)</h3>
    <table aria-label="Gas Phase Heat Capacity (Shomate Equation)" class="data" style="width: 50.00%;">
      <tr>
        <th scope="row" style="text-align: left;">Temperature (K)</th>
        <td class="exp">500. to 1700.</td>
        <td class="exp">1700. to 6000.</td>
      </tr>
      <tr>
        <th scope="row" style="text-align: left;">A</th>
        <td class="exp">30.09200</td>
        <td class="exp">41.96426</td>
      </tr>
      <tr>
        <th scope="row" style="text-align: left;">B</th>
        <td class="exp">6.832514</td>
        <td class="exp">8.622053</td>
      </tr>
      <tr>
        <th scope="row" style="text-align: left;">C</th>
        <td class="exp">6.793435</td>
        <td class="exp">-1.499780</td>
      </tr>
      <tr>
        <th scope="row" style="text-align: left;">D</th>
        <td class="exp">-2.534480</td>
        <td class="exp">0.098119</td>
      </tr>
      <tr>
        <th scope="row" style="text-align: left;">E</th>
        <td class="exp">0.082139</td>
        <td class="exp">-11.15764</td>
      </tr>
      <tr>
        <th scope="row" style="text-align: left;">F</th>
        <td class="exp">-250.8810</td>
        <td class="exp">-272.1797</td>
      </tr>
      <tr>
        <th scope="row" style="text-align: left;">G</th>
        <td class="exp">223.3967</td>
        <td class="exp">219.7809</td>
      </tr>
      <tr>
        <th scope="row" style="text-align: left;">H</th>
        <td class="exp">-241.8264</td>
        <td class="exp">-241.8264</td>
      </tr>
    </table>
    """

@pytest.fixture
def mock_thermo_page_html():
    return """
    <html>
      <head><title>Water</title></head>
      <body>
        <h1 id="Top">Water</h1>
        <ul>
          <li><strong>Formula:</strong> H<sub>2</sub>O</li>
          <li><strong>Molecular weight:</strong> 18.0153</li>
          <li><strong>CAS Registry Number:</strong> 7732-18-5</li>
        </ul>
        
        <h2 id="Thermo-Gas">Gas phase thermochemistry data</h2>
        <table class="data">
          <tr>
            <th>Quantity</th>
            <th>Value</th>
            <th>Units</th>
            <th>Method</th>
          </tr>
          <tr class="exp">
            <td>Δ<sub>f</sub>H°<sub>gas</sub></td>
            <td class="right-nowrap">-241.826 ± 0.040</td>
            <td>kJ/mol</td>
            <td>Review</td>
          </tr>
          <tr class="exp">
            <td>S°<sub>gas,1 bar</sub></td>
            <td class="right-nowrap">188.835 ± 0.010</td>
            <td>J/mol*K</td>
            <td>Review</td>
          </tr>
        </table>
        
        <h3>Gas Phase Heat Capacity (Shomate Equation)</h3>
        <table aria-label="Gas Phase Heat Capacity (Shomate Equation)" class="data">
          <tr>
            <th>Temperature (K)</th>
            <td>500. to 1700.</td>
          </tr>
          <tr>
            <th>A</th>
            <td>30.09200</td>
          </tr>
          <tr>
            <th>B</th>
            <td>6.832514</td>
          </tr>
          <tr>
            <th>C</th>
            <td>6.793435</td>
          </tr>
          <tr>
            <th>D</th>
            <td>-2.534480</td>
          </tr>
          <tr>
            <th>E</th>
            <td>0.082139</td>
          </tr>
          <tr>
            <th>F</th>
            <td>-250.8810</td>
          </tr>
          <tr>
            <th>G</th>
            <td>223.3967</td>
          </tr>
          <tr>
            <th>H</th>
            <td>-241.8264</td>
          </tr>
        </table>
      </body>
    </html>
    """

@pytest.fixture
def mock_phase_page_html():
    return """
    <html>
      <head><title>Ethanol</title></head>
      <body>
        <h1 id="Top">Ethanol</h1>
        <h2 id="Thermo-Phase">Phase change data</h2>
        <table class="data">
          <tr>
            <th>Quantity</th>
            <th>Value</th>
            <th>Units</th>
          </tr>
          <tr class="cal">
            <td>T<sub>boil</sub></td>
            <td class="right-nowrap">351.5 ± 0.2</td>
            <td>K</td>
          </tr>
          <tr class="cal">
            <td>T<sub>fus</sub></td>
            <td class="right-nowrap">159. ± 2.</td>
            <td>K</td>
          </tr>
          <tr class="cal">
            <td>Δ<sub>vap</sub>H°</td>
            <td class="right-nowrap">42.3 ± 0.4</td>
            <td>kJ/mol</td>
          </tr>
        </table>
        
        <h3>Antoine Equation Parameters</h3>
        <table class="data">
          <tr>
            <th>Temperature (K)</th>
            <th>A</th>
            <th>B</th>
            <th>C</th>
          </tr>
          <tr>
            <td>364.8 to 513.91</td>
            <td>4.92531</td>
            <td>1432.526</td>
            <td>-61.819</td>
          </tr>
        </table>
        
        <h3>Enthalpy of fusion</h3>
        <table class="data">
          <tr>
            <th>Δ<sub>fus</sub>H (kJ/mol)</th>
            <th>Temperature (K)</th>
          </tr>
          <tr>
            <td>4.973</td>
            <td>159.</td>
          </tr>
        </table>
      </body>
    </html>
    """
