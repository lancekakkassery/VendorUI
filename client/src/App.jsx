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

{/*
<button onClick={() => setCount((count) => count + 1)}>
  count is {count}
</button>
*/} 
function App() {
  const [count, setCount] = useState(0)

  const fetchSalesData = async () =>{
    const response = await axios.get('http://127.0.0.1:8080/sales');
    console.log(response.data)
  }
  const fetchProductsData = async () =>{
    const response = await axios.get('http://127.0.0.1:8080/products');
    console.log(response.data)
  }
  const fetchOrderHistory = async () =>{
    const response = await axios.get('http://127.0.0.1:8080/order_history');
    console.log(response.data)
  }


  useEffect(() =>{
    fetchSalesData()
    fetchProductsData()
  },[])

  return (
    <>
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
              labels:["Lettuce","Tomatoes","Buns"],
              datasets:[
                {
                  label:"Stock",
                  data:[200,300,400]
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
        position: 'absolute',
        top:'10%',
        left: '10%'
      }}>
        <div className = 'sales'>
          <Line
            data = {{
              labels:['12','1','2','3','4','5','6','7','8','9','10'],
              datasets:[{
                label:'Todays Revenue',
                data:[702, 1194, 1494, 513, 1135, 1297, 1387, 859, 1490, 826, 970]
              }]

            }}
          />
          <Line
            data = {{
              labels:['January', 'Febuary','March','April','May','June','July','August','September','October','November','December'],
              datasets:[{
                label:'Monthly Revenue',
                data:[998, 1133, 955, 931, 1265, 756, 554, 730, 1170, 1490, 1418,1300]
              }]

            }}
            options={{
              maintainAspectRatio:false,
              responsive:true
            }}
          />
        </div>
      </div>
    </>
  )
}

export default App
