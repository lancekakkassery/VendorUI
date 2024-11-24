import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import Navbarbar from './Navbar.jsx'
import axios from 'axios'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Link } from 'react-router-dom'
import { Chart as ChartJS, defaults } from "chart.js/auto";
import { Bar, Doughnut, Line } from "react-chartjs-2";
import Cashier from "./Cashier.jsx"

{/*
<button onClick={() => setCount((count) => count + 1)}>
  count is {count}
</button>
*/} 
function App() {
  const [currentScreen, setCurrentScreen] = useState('home')

  const [products, setProducts] = useState([])
  const [sales, setSales] = useState([])
  const [orders, setOrders] = useState([])

  const fetchSalesData = async () =>{
    const response = await axios.get('http://127.0.0.1:8080/sales');
    console.log(response.data)
    setSales(response.data)
  }
  const fetchProductsData = async () =>{
    const response = await axios.get('http://127.0.0.1:8080/inventory');
    console.log(response.data)
    setProducts(response.data)
  }
  const fetchOrderHistory = async () =>{
    const response = await axios.get('http://127.0.0.1:8080/order_history');
    console.log(response.data)
    setOrders(response.data)
  }


  useEffect(() =>{
    fetchSalesData()
    fetchProductsData()
    fetchOrderHistory()
  },[])

  const hourlySales = {}
  // Loop through the sales data
  sales.forEach((sale) => {
  // Extract the hour from the sale_date_time
  const hour = new Date(sale.sale_date_time).getHours();

  // Ensure there is an entry for this hour
  if (!hourlySales[hour]) {
    hourlySales[hour] = { count: 0, total: 0 };
  }

  // Increment the count and total for the corresponding hour
  hourlySales[hour].count += 1;
  hourlySales[hour].total += sale.total;
});
  console.log(hourlySales);
  console.log(currentScreen)
  return (
    <>
    {currentScreen === 'home' && (
      <div>
      <button onClick={() => setCurrentScreen('Cashier')}>Go to Cashier</button>
      </div>
    )}
    {currentScreen === "Cashier" && (
      <div>
        <Cashier/>
        <button onClick = {() => setCurrentScreen('home')}>Go Back to Home</button>
      </div>
    )}
    {/* item stock*/} 
      <div className="card" 
      style={{
        position: 'absolute',
        top:'10%',
        right:'10%'
      }}>
        <div style={{
          height:'18rem',
          justifyContent:'stretch'
        }}>
          <Bar
            data = {{
              labels:products.map((data) => data.product_name),
              datasets:[
                {
                  label:"Stock",
                  data:products.map((data) => data.quantity),
                }
              ]
            }}
            options={{
              maintainAspectRatio:false, 
            }}
          />
        </div>
      </div>

      <div className="card"
      style={{
        position: 'absolute',
        top:'57%',
        right:'10%'
      }}>
        <div className = 'doughnut content'>
          <Doughnut
          data = {{
            labels:[
                'Unmarked Secret Shoppers',
                'Finished',
                'Perfect Shops'
              ],
              datasets: [{
                label: 'My First Dataset',
                data: [10, 5, 3],
                backgroundColor: [
                  'rgb(255, 99, 132)',
                  'rgb(54, 162, 235)',
                  'rgb(255, 205, 86)'
                ],
                hoverOffset: 4
              }]
            }}
          
          />
        </div>
      </div>

{/* sales */} 
      <div className="card"
      style={{
        position:'absolute',
        top:'10%',
        left: '10%'
      }}>
        {/*Daily Sales */}
        
        <div className = 'sales'>
          <Line
            data = {{
              labels:['12','1','2','3','4','5','6','7','8','9','10',],
              datasets:[{
                label:'$',
                data:[702, 1194, 1494, 513, 1135, 1297, 1387, 859, 1490, 826, 970],
                borderColor: 'green',
                fill: true,
                backgroundColor: 'rgba(0, 128, 0, 0.2)'
              }]

            }}
            options={{
              maintainAspectRatio:false,
              responsive:true,
              plugins:{
                title:{
                  display:true,
                  text:'Daily Revenue'
                }
              }
            }}
          />
          {/*Number of Orders */}
        </div>
      </div>

      <div className='card'
      style={{
        position:'absolute',
        left:'10%',
        top:'55%'
      }}>
        <div className='sales'>
          <Line
            data = {{
              labels:['12','1','2','3','4','5','6','7','8','9','10'],
              datasets:[{
                label:'Quantity',
                data:[998, 1133, 955, 931, 1265, 756, 554, 730, 1170, 1490, 1418,1300],
                borderColor: 'rgba(137, 196, 244)',
                fill: true,
                backgroundColor: 'rgba(137, 196, 244,.2)'
              }]

            }}
            options={{
              maintainAspectRatio:false,
              responsive:true,
              plugins:{
                title:{
                  display:true,
                  text:'Daily Orders'
                }
              }
            }}
          />
          </div>
        </div>
    </>
  )
}

export default App
